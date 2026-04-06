#!/usr/bin/env python3
"""Plot NIfTI images under /deneb_disk/disc_mri/magma/ and save PNGs.

Walks the source directory (recursively by default), finds .nii and .nii.gz
files and creates orthogonal view PNGs using nilearn.plotting.plot_anat.

Example:
  python scripts/plot_magma_nifti.py --src /deneb_disk/disc_mri/magma --dst ./magma_plots

"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import glob
import sys
import shutil
import warnings

import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt
from nilearn import plotting, image
from PIL import Image, ImageChops


def find_nifti_files(root: Path, pattern: str | None = None, recursive: bool = True):
    exts = (".nii", ".nii.gz")
    if recursive:
        for dirpath, dirs, files in os.walk(root):
            for fn in files:
                if fn.endswith('.nii') or fn.endswith('.nii.gz'):
                    if pattern and pattern not in fn:
                        continue
                    if 'mask' in fn.lower():
                        continue
                    yield Path(dirpath) / fn
    else:
        for p in root.iterdir():
            if p.suffix in exts or p.name.endswith('.nii.gz'):
                if pattern and pattern not in p.name:
                    continue
                if 'mask' in p.name.lower():
                    continue
                yield p


def clean_figure(fig):
    # remove titles/texts and tiny colorbars like existing plotting script
    for ax in fig.axes:
        for txt in list(ax.texts):
            try:
                txt.set_visible(False)
            except Exception:
                pass

    for extra_ax in list(fig.axes):
        pos = extra_ax.get_position()
        if pos.width < 0.06 or pos.height < 0.06:
            try:
                fig.delaxes(extra_ax)
            except Exception:
                pass


def make_output_path(src_path: Path, src_root: Path, dst_root: Path) -> Path:
    rel = src_path.relative_to(src_root)
    out = dst_root / rel.with_suffix('.png')
    out.parent.mkdir(parents=True, exist_ok=True)
    return out


def plot_file(img_input, out_path: Path, dpi: int = 300, display_mode: str = 'ortho', cut_coords=None) -> None:
    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(111)
    try:
        # Crop the image to its non-zero bounds to zoom in on the content
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cropped_img = image.crop_img(img_input)
            
            plotting.plot_anat(cropped_img, axes=ax,
                               title=None,
                               display_mode=display_mode, dim=-1, annotate=False, draw_cross=False,
                               colorbar=False, cut_coords=cut_coords)

        ax.set_title("")
        clean_figure(fig)
        plt.savefig(str(out_path), dpi=dpi, bbox_inches='tight', pad_inches=0, facecolor='black')
    finally:
        plt.close(fig)

    # Crop the saved PNG to content (remove black or white padding)
    try:
        img_pn = Image.open(str(out_path))
        # find bounding box of non-black pixels
        bg = Image.new("RGB", img_pn.size, (0, 0, 0))
        diff = ImageChops.difference(img_pn.convert("RGB"), bg)
        bbox = diff.getbbox()
        if bbox:
            img_cropped = img_pn.crop(bbox)
            img_cropped.save(str(out_path))
    except Exception as e:
        warnings.warn(f"Failed to post-crop PNG {out_path}: {e}")


def find_mask_for_image(img_path: Path) -> Path | None:
    """Search for a mask file in the same directory as img_path.

    Heuristics:
    - exact stem + '_mask' or stem + 'mask' variants
    - any file in dir containing 'mask' or 'brain' in the name
    Returns Path or None.
    """
    d = img_path.parent
    stem = img_path.stem
    # consider compressed name stem for .nii.gz (stem removes only .gz), handle that
    candidates = []
    patterns = [f"{stem}_mask*.nii*", f"{stem}mask*.nii*", f"{stem}*_brain*.nii*", "*mask*.nii*", "*brain_mask*.nii*"]
    for pat in patterns:
        for p in d.glob(pat):
            candidates.append(p)

    # remove the image itself if matched
    candidates = [p for p in candidates if p.resolve() != img_path.resolve()]
    if not candidates:
        return None

    # prefer candidates that contain the stem
    for p in candidates:
        if stem in p.stem:
            return p
    return candidates[0]


def apply_mask_to_image(img_path: Path, mask_path: Path):
    """Return a Nifti1Image with mask applied, handling potential affine differences."""
    try:
        resampled_mask = image.resample_to_img(str(mask_path), str(img_path), interpolation='nearest', force_resample=True, copy_header=True)
    except TypeError: # Older nilearn
        resampled_mask = image.resample_to_img(str(mask_path), str(img_path), interpolation='nearest')
    return image.math_img("img * (mask > 0)", img=str(img_path), mask=resampled_mask)


def main(argv=None):
    p = argparse.ArgumentParser(description="Plot NIfTI images under a directory and save PNGs.")
    p.add_argument('--src', default='/deneb_disk/disc_mri/magma', help='Source directory to scan')
    p.add_argument('--dst', default='./magma_plots', help='Destination directory for PNGs')
    p.add_argument('--pattern', default=None, help='Optional substring pattern to filter filenames')
    p.add_argument('--recursive', action='store_true', default=True, help='Recursively scan source (default)')
    p.add_argument('--no-recursive', dest='recursive', action='store_false', help='Do not recurse')
    p.add_argument('--dpi', type=int, default=300, help='Output PNG DPI')
    p.add_argument('--display-mode', default='ortho', help='nilearn display_mode (default: ortho)')
    p.add_argument('--dry-run', action='store_true', help='List files that would be plotted')
    args = p.parse_args(argv)

    src_root = Path(args.src)
    dst_root = Path(args.dst)
    if not src_root.exists():
        print(f"Source not found: {src_root}")
        return 2

    files = list(find_nifti_files(src_root, pattern=args.pattern, recursive=args.recursive))
    if not files:
        print("No NIfTI files found.")
        return 0

    print(f"Found {len(files)} files.\n")

    from collections import defaultdict
    dirs_to_files = defaultdict(list)
    for f in files:
        dirs_to_files[f.parent].append(f)

    for d, d_files in dirs_to_files.items():
        # Find a common cut_coord for this directory to ensure same viewpoint
        common_cut_coords = None
        ref_mask = find_mask_for_image(d_files[0])
        if ref_mask:
            try:
                common_cut_coords = plotting.find_cut_coords(str(ref_mask))
            except Exception:
                pass
        
        if common_cut_coords is None:
            try:
                common_cut_coords = plotting.find_cut_coords(str(d_files[0]))
            except Exception:
                pass

        for fp in d_files:
            try:
                outp = make_output_path(fp, src_root, dst_root)
                mask = find_mask_for_image(fp)
                if args.dry_run:
                    if mask:
                        print(f"Would plot (with mask): {fp} + {mask} -> {outp}")
                    else:
                        print(f"Would plot: {fp} -> {outp}")
                    continue

                print(f"Plotting: {fp} -> {outp} (cut_coords: {common_cut_coords})")
                if mask:
                    try:
                        masked_img = apply_mask_to_image(fp, mask)
                        plot_file(masked_img, outp, dpi=args.dpi, display_mode=args.display_mode, cut_coords=common_cut_coords)
                    except Exception as e:
                        warnings.warn(f"Failed applying mask {mask} to {fp}: {e}. Falling back to raw image.")
                        plot_file(fp, outp, dpi=args.dpi, display_mode=args.display_mode, cut_coords=common_cut_coords)
                else:
                    plot_file(fp, outp, dpi=args.dpi, display_mode=args.display_mode, cut_coords=common_cut_coords)
            except Exception as e:
                warnings.warn(f"Failed plotting {fp}: {e}")

    print("Done.")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
