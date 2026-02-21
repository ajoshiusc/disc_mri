"""
Estimate T2* map from coregistered multi-echo fetal T2-weighted MRI images.

Model: S(TE) = S0 * exp(-TE / T2*)

Given 4 coregistered images acquired at different TE values, this script
performs a voxel-wise log-linear fit to estimate T2* and S0 maps.

Usage:
    python main_estimate_t2star.py

Adjust the file paths and TE values below to match your data.
"""

import os
import numpy as np
import nibabel as nib
from scipy.optimize import curve_fit

# ============================================================
# USER SETTINGS — edit these to match your data
# ============================================================

# Echo times in milliseconds (must match the order of input files)
TE_values = np.array([98.0, 140.0, 181.0, 272.0])  # ms

# Coregistered NIfTI images (one per TE), all in the same space
input_dir = '/deneb_disk/disc_mri/fetal_mri_te_images'
input_files = [
    os.path.join(input_dir, 'te98.nii.gz'),
    os.path.join(input_dir, 'te140.nii.gz'),
    os.path.join(input_dir, 'te181.nii.gz'),
    os.path.join(input_dir, 'te272.nii.gz'),
]

# Output directory and filenames
output_dir = '/deneb_disk/disc_mri/fetal_mri_te_images'
t2star_output = os.path.join(output_dir, 'T2star_map.nii.gz')
s0_output = os.path.join(output_dir, 'S0_map.nii.gz')
r2star_output = os.path.join(output_dir, 'R2star_map.nii.gz')

# Signal threshold: voxels below this fraction of the max signal are masked out
signal_threshold_fraction = 0.05

# T2* clipping range (ms) — values outside this range are set to 0
T2STAR_MIN = 1.0    # ms
T2STAR_MAX = 500.0  # ms

# ============================================================
# FUNCTIONS
# ============================================================

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

    # Build mask: all echoes must be positive
    mask = np.all(voxels > 0, axis=1)

    # Log-transform
    log_signal = np.zeros_like(voxels)
    log_signal[mask] = np.log(voxels[mask])

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
    print("T2* Estimation from Multi-Echo Fetal MRI")
    print("=" * 60)

    # --- Load images ---
    print("\nLoading images...")
    imgs = []
    ref_img = None
    for i, fpath in enumerate(input_files):
        print(f"  TE={TE_values[i]:.1f} ms : {fpath}")
        nii = nib.load(fpath)
        if ref_img is None:
            ref_img = nii
        imgs.append(nii.get_fdata().astype(np.float64))

    # Stack into 4D: (nx, ny, nz, n_echoes)
    images = np.stack(imgs, axis=-1)
    print(f"  Image shape: {images.shape}")

    # --- Create brain mask ---
    print("\nCreating signal mask...")
    mean_img = images.mean(axis=-1)
    signal_threshold = signal_threshold_fraction * mean_img.max()
    brain_mask = mean_img > signal_threshold
    n_voxels = brain_mask.sum()
    print(f"  Threshold: {signal_threshold:.1f}")
    print(f"  Masked voxels: {n_voxels}")

    # Zero out background
    images[~brain_mask] = 0

    # --- Log-linear T2* estimation ---
    print("\nStep 1: Log-linear T2* estimation...")
    t2star_map, s0_map = estimate_t2star_loglinear(images, TE_values)

    # --- NLLS refinement ---
    print("\nStep 2: Non-linear least squares refinement...")
    t2star_map, s0_map = estimate_t2star_nlls(images, TE_values, t2star_map, s0_map)

    # --- Clip and clean ---
    print("\nCleaning T2* map...")
    t2star_map[~brain_mask] = 0
    t2star_map[(t2star_map < T2STAR_MIN) | (t2star_map > T2STAR_MAX)] = 0
    s0_map[~brain_mask] = 0

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
