"""
Coregister multi-echo SVR-reconstructed fetal T2-weighted MRI using FSL flirt,
then estimate T2* map via mono-exponential fitting.

Model: S(TE) = S0 * exp(-TE / T2*)

Pipeline:
  1. Auto-select the SVR image with the highest number of stacks per TE.
  2. Register TE=140, 181, 272 SVRs to the TE=98 reference using FSL flirt
     (6-DOF rigid body, correlation ratio cost, sinc interpolation).
  3. Voxel-wise log-linear fit → T2* and S0 initial estimates.
  4. Non-linear least-squares refinement (Levenberg-Marquardt).
  5. Save T2*, S0, R2* maps as NIfTI.

Usage:
    python main_estimate_t2star.py
"""

import os
import re
import glob
import subprocess
import numpy as np
import nibabel as nib
from scipy.optimize import curve_fit
from scipy.ndimage import median_filter

# ============================================================
# USER SETTINGS
# ============================================================

# Echo times in milliseconds
TE_values = np.array([98.0, 140.0, 181.0, 272.0])  # ms

# SVR output directory for scan_8_11_2023
svr_dir = '/deneb_disk/disc_mri/scan_8_11_2023/outsvr'

# Iteration index to pick (0 = first random combination at that stack count)
ITER_TO_USE = 0

# The first TE (TE=98) is the reference for coregistration
reference_idx = 0

# Output directory
output_dir = '/deneb_disk/disc_mri/scan_8_11_2023/t2star_output'
t2star_output = os.path.join(output_dir, 'T2star_map.nii.gz')
s0_output = os.path.join(output_dir, 'S0_map.nii.gz')
r2star_output = os.path.join(output_dir, 'R2star_map.nii.gz')

# Signal threshold: voxels below this fraction of the max signal are masked out
signal_threshold_fraction = 0.05

# T2* clipping range (ms) — values outside this range are set to 0
T2STAR_MIN = 1.0    # ms
T2STAR_MAX = 2000.0 # ms  (CSF in ventricles can be >1000 ms)

# Set to True to refine with NLLS (slow for large SVR volumes)
USE_NLLS_REFINEMENT = False


def find_max_stacks_svr(svr_dir, te, iter_idx=0):
    """
    Find the SVR file with the highest numstacks for a given TE.

    Looks for files matching:  svr_te{te}_numstacks_{N}_iter_{iter_idx}.nii.gz
    (excluding *_aligned.nii.gz and *_masked.nii.gz)

    Returns the path to the file with the largest N.
    """
    pattern = os.path.join(svr_dir, f'svr_te{te}_numstacks_*_iter_{iter_idx}.nii.gz')
    candidates = glob.glob(pattern)
    # Filter out aligned / masked variants
    candidates = [c for c in candidates if '_aligned' not in c and '_masked' not in c]

    if not candidates:
        raise FileNotFoundError(f"No SVR files found for TE={te}, iter={iter_idx} in {svr_dir}")

    # Extract numstacks and find max
    def get_numstacks(path):
        m = re.search(r'numstacks_(\d+)', os.path.basename(path))
        return int(m.group(1)) if m else 0

    best = max(candidates, key=get_numstacks)
    print(f"  TE={te:>3d} ms : numstacks={get_numstacks(best):>2d}  ->  {os.path.basename(best)}")
    return best

# ============================================================
# FUNCTIONS
# ============================================================


def coregister_with_flirt(input_files, reference_idx, output_dir):
    """
    Coregister all images to a common reference using FSL flirt.

    Parameters
    ----------
    input_files : list of str
        Paths to input NIfTI files.
    reference_idx : int
        Index of the reference image (not registered, just copied).
    output_dir : str
        Directory for coregistered outputs and transform matrices.

    Returns
    -------
    coreg_files : list of str
        Paths to the coregistered NIfTI files (in reference space).
    """
    coreg_dir = os.path.join(output_dir, 'coregistered')
    os.makedirs(coreg_dir, exist_ok=True)

    ref_file = input_files[reference_idx]
    coreg_files = []

    for i, inp in enumerate(input_files):
        basename = os.path.basename(inp).replace('.nii.gz', '')
        out_file = os.path.join(coreg_dir, f'{basename}_coreg.nii.gz')
        omat_file = os.path.join(coreg_dir, f'{basename}_coreg.mat')

        if i == reference_idx:
            # Reference image — just copy it
            if os.path.exists(out_file):
                print(f"  [TE idx {i}] Reference already exists — skipping copy.")
            else:
                print(f"  [TE idx {i}] Reference image — copying: {os.path.basename(inp)}")
                cmd = ['cp', inp, out_file]
                subprocess.run(cmd, check=True)
        else:
            if os.path.exists(out_file):
                print(f"  [TE idx {i}] Already coregistered — skipping: {os.path.basename(out_file)}")
            else:
                print(f"  [TE idx {i}] Registering {os.path.basename(inp)} -> reference ...")
                cmd = [
                    'flirt',
                    '-in', inp,
                    '-ref', ref_file,
                    '-out', out_file,
                    '-omat', omat_file,
                    '-dof', '6',                  # rigid body
                    '-cost', 'corratio',           # correlation ratio
                    '-searchrx', '-30', '30',
                    '-searchry', '-30', '30',
                    '-searchrz', '-30', '30',
                    '-interp', 'sinc',
                ]
                print(f"    CMD: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"    FLIRT STDERR: {result.stderr}")
                    raise RuntimeError(f"flirt failed for {inp}")
                print(f"    Done -> {os.path.basename(out_file)}")

        coreg_files.append(out_file)

    return coreg_files

def mono_exponential(te, s0, r2star):
    """Mono-exponential decay: S = S0 * exp(-TE * R2*)."""
    return s0 * np.exp(-te * r2star)


def estimate_t2star_loglinear(images, te_values):
    """
    Estimate T2* using a log-linear (weighted least squares) fit.

    ln(S) = ln(S0) - TE / T2*

    Parameters
    ----------
    images : np.ndarray, shape (nx, ny, nz, n_echoes)
        Multi-echo image data.
    te_values : np.ndarray, shape (n_echoes,)
        Echo times in milliseconds.

    Returns
    -------
    t2star_map : np.ndarray, shape (nx, ny, nz)
    s0_map : np.ndarray, shape (nx, ny, nz)
    """
    n_echoes = len(te_values)
    shape = images.shape[:3]

    # Flatten spatial dims for vectorised fitting
    voxels = images.reshape(-1, n_echoes).astype(np.float64)

    # Build mask: any voxel that is not all-zero across echoes
    mask = np.any(voxels != 0, axis=1)

    # Log-transform (clamp to small epsilon to avoid log(0))
    eps = 1e-10
    log_signal = np.zeros_like(voxels)
    log_signal[mask] = np.log(np.maximum(voxels[mask], eps))

    # Design matrix for linear regression: ln(S) = a + b*TE
    # where a = ln(S0), b = -1/T2*
    A = np.column_stack([np.ones(n_echoes), te_values])

    # Solve least squares for all masked voxels at once
    # log_signal[mask] has shape (n_masked_voxels, n_echoes)
    # We need to solve A @ [a, b]^T = log_signal^T for each voxel
    # Using pseudoinverse: params = (A^T A)^-1 A^T y
    ATA_inv_AT = np.linalg.pinv(A)  # shape (2, n_echoes)

    params = np.zeros((voxels.shape[0], 2))
    params[mask] = (ATA_inv_AT @ log_signal[mask].T).T

    # Extract maps
    s0_flat = np.exp(params[:, 0])
    slope = params[:, 1]  # = -1/T2*

    # T2* = -1 / slope (slope should be negative for decay)
    t2star_flat = np.zeros(voxels.shape[0])
    valid_slope = mask & (slope < 0)
    t2star_flat[valid_slope] = -1.0 / slope[valid_slope]

    # Voxels with slope >= 0 have no measurable decay → very long T2*
    # (e.g. CSF in ventricles). Assign T2STAR_MAX instead of 0.
    no_decay = mask & (slope >= 0)
    t2star_flat[no_decay] = T2STAR_MAX

    # Reshape
    t2star_map = t2star_flat.reshape(shape)
    s0_map = s0_flat.reshape(shape)

    return t2star_map, s0_map


def estimate_t2star_nlls(images, te_values, t2star_init, s0_init):
    """
    Refine T2* estimates using non-linear least squares (Levenberg-Marquardt).

    Uses the log-linear estimates as initial guesses. Only fits voxels
    where the initial estimate is within a valid range.

    Parameters
    ----------
    images : np.ndarray, shape (nx, ny, nz, n_echoes)
    te_values : np.ndarray, shape (n_echoes,)
    t2star_init : np.ndarray, shape (nx, ny, nz)
    s0_init : np.ndarray, shape (nx, ny, nz)

    Returns
    -------
    t2star_map : np.ndarray, shape (nx, ny, nz)
    s0_map : np.ndarray, shape (nx, ny, nz)
    """
    shape = images.shape[:3]
    n_echoes = len(te_values)

    voxels = images.reshape(-1, n_echoes).astype(np.float64)
    t2_init_flat = t2star_init.ravel()
    s0_init_flat = s0_init.ravel()

    t2star_flat = t2_init_flat.copy()
    s0_flat = s0_init_flat.copy()

    # Only refine voxels with valid initial estimates
    mask = (t2_init_flat > T2STAR_MIN) & (t2_init_flat < T2STAR_MAX) & (s0_init_flat > 0)
    indices = np.where(mask)[0]

    print(f"  Refining {len(indices)} voxels with NLLS...")

    for count, idx in enumerate(indices):
        if count % 50000 == 0 and count > 0:
            print(f"    {count}/{len(indices)} voxels fitted...")

        y = voxels[idx]
        s0_guess = s0_init_flat[idx]
        r2star_guess = 1.0 / t2_init_flat[idx]

        try:
            popt, _ = curve_fit(
                mono_exponential,
                te_values,
                y,
                p0=[s0_guess, r2star_guess],
                bounds=([0, 0], [np.inf, 1.0 / T2STAR_MIN]),
                maxfev=500,
            )
            s0_flat[idx] = popt[0]
            t2star_flat[idx] = 1.0 / popt[1] if popt[1] > 0 else 0.0
        except (RuntimeError, ValueError):
            # Keep the log-linear estimate
            pass

    return t2star_flat.reshape(shape), s0_flat.reshape(shape)


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("T2* Estimation from Multi-Echo Fetal MRI (SVR)")
    print("  scan_8_11_2023  —  highest numstacks SVR per TE")
    print("  with FSL FLIRT coregistration")
    print("=" * 60)

    os.makedirs(output_dir, exist_ok=True)

    # --- Step 0a: Auto-select best SVR per TE ---
    print(f"\nSelecting SVR images (iter={ITER_TO_USE}) with max stacks from:")
    print(f"  {svr_dir}")
    input_files = []
    for te in TE_values:
        svr_file = find_max_stacks_svr(svr_dir, int(te), iter_idx=ITER_TO_USE)
        input_files.append(svr_file)

    # --- Step 0b: Coregister with FSL flirt ---
    print("\nCoregistering images with FSL flirt ...")
    print(f"  Reference: TE={TE_values[reference_idx]:.0f} ms — {os.path.basename(input_files[reference_idx])}")
    coreg_files = coregister_with_flirt(input_files, reference_idx, output_dir)

    # --- Load coregistered images ---
    print("\nLoading coregistered images...")
    imgs = []
    ref_img = None
    for i, fpath in enumerate(coreg_files):
        print(f"  TE={TE_values[i]:.1f} ms : {fpath}")
        nii = nib.load(fpath)
        if ref_img is None:
            ref_img = nii
        imgs.append(nii.get_fdata().astype(np.float64))

    # Stack into 4D: (nx, ny, nz, n_echoes)
    images = np.stack(imgs, axis=-1)
    print(f"  Image shape: {images.shape}")

    # --- Create mask: voxels with positive signal in ALL 4 echoes ---
    # Voxels with partial echo coverage (from coregistration boundary) give
    # unreliable fits, so we require all echoes > 0.
    print("\nCreating mask (all 4 echoes > 0)...")
    brain_mask = np.all(images > 0, axis=-1)
    n_voxels = brain_mask.sum()
    n_any = np.any(images != 0, axis=-1).sum()
    print(f"  Voxels with any signal:  {n_any}")
    print(f"  Voxels with all 4 echoes > 0: {n_voxels} (used for fitting)")

    # --- Log-linear T2* estimation ---
    print("\nStep 1: Log-linear T2* estimation...")
    t2star_map, s0_map = estimate_t2star_loglinear(images, TE_values)

    # --- NLLS refinement (optional — slow for large SVR volumes) ---
    if USE_NLLS_REFINEMENT:
        print("\nStep 2: Non-linear least squares refinement...")
        t2star_map, s0_map = estimate_t2star_nlls(images, TE_values, t2star_map, s0_map)
    else:
        print("\nStep 2: NLLS refinement skipped (USE_NLLS_REFINEMENT=False).")

    # --- Clip and clean ---
    print("\nCleaning T2* map...")
    t2star_map[~brain_mask] = 0
    t2star_map[(t2star_map < T2STAR_MIN) | (t2star_map > T2STAR_MAX)] = 0
    s0_map[~brain_mask] = 0

    # --- Fill scattered blank voxels with iterative median filter ---
    print("Filling zero voxels within mask using iterative 3D median filter...")
    zero_holes = brain_mask & (t2star_map == 0)
    n_holes_initial = zero_holes.sum()
    print(f"  Zero-holes in mask before filling: {n_holes_initial}")

    if n_holes_initial > 0:
        max_iterations = 10
        for iteration in range(max_iterations):
            t2star_filtered = median_filter(t2star_map, size=3)
            zero_holes = brain_mask & (t2star_map == 0)
            n_before = zero_holes.sum()
            if n_before == 0:
                break
            t2star_map[zero_holes] = t2star_filtered[zero_holes]
            n_after = (brain_mask & (t2star_map == 0)).sum()
            filled = n_before - n_after
            print(f"    Iter {iteration+1}: filled {filled} voxels, remaining {n_after}")
            if filled == 0:
                break

        # Also fill S0 the same way
        for iteration in range(max_iterations):
            s0_holes = brain_mask & (s0_map == 0)
            if s0_holes.sum() == 0:
                break
            s0_filtered = median_filter(s0_map, size=3)
            s0_map[s0_holes] = s0_filtered[s0_holes]
            if (brain_mask & (s0_map == 0)).sum() == s0_holes.sum():
                break

        remaining = (brain_mask & (t2star_map == 0)).sum()
        print(f"  Final zero-holes remaining: {remaining} / {n_holes_initial} filled")

    # R2* = 1000 / T2* (in s^-1, with T2* in ms)
    r2star_map = np.zeros_like(t2star_map)
    valid = t2star_map > 0
    r2star_map[valid] = 1000.0 / t2star_map[valid]

    # --- Print summary statistics ---
    valid_t2 = t2star_map[brain_mask & (t2star_map > 0)]
    if len(valid_t2) > 0:
        print(f"\n  T2* statistics (within mask):")
        print(f"    Median : {np.median(valid_t2):.1f} ms")
        print(f"    Mean   : {np.mean(valid_t2):.1f} ms")
        print(f"    Std    : {np.std(valid_t2):.1f} ms")
        print(f"    Range  : [{np.min(valid_t2):.1f}, {np.max(valid_t2):.1f}] ms")

    # --- Save outputs ---
    print(f"\nSaving outputs to: {output_dir}")
    os.makedirs(output_dir, exist_ok=True)

    affine = ref_img.affine
    header = ref_img.header

    t2star_nii = nib.Nifti1Image(t2star_map.astype(np.float32), affine, header)
    nib.save(t2star_nii, t2star_output)
    print(f"  T2* map  : {t2star_output}")

    s0_nii = nib.Nifti1Image(s0_map.astype(np.float32), affine, header)
    nib.save(s0_nii, s0_output)
    print(f"  S0 map   : {s0_output}")

    r2star_nii = nib.Nifti1Image(r2star_map.astype(np.float32), affine, header)
    nib.save(r2star_nii, r2star_output)
    print(f"  R2* map  : {r2star_output}")

    print("\nDone.")


if __name__ == '__main__':
    main()
