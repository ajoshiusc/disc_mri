
import os
import glob
import matplotlib
matplotlib.use('Agg')  # Force non-interactive backend
from nilearn import plotting, image
import nibabel as nib
import matplotlib.pyplot as plt
import sys

# Force output buffering off
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

import numpy as np

def permute_to_z(img, axis):
    """
    Permutes the image axes so that the specified axis becomes the Z-axis (2).
    This allows using display_mode='mosaic' (which cuts along Z) for other axes.
    """
    if axis == 'z':
        return img
    
    # Get original data and affine
    data = img.get_fdata()
    affine = img.affine

    new_affine = affine.copy()
    if axis == 'x':
        new_data = np.transpose(data, (2, 1, 0))
        # Swap columns 0 (X) and 2 (Z)
        new_affine[:, [0, 2]] = new_affine[:, [2, 0]]
    elif axis == 'y':
        new_data = np.transpose(data, (0, 2, 1))
        # Swap columns 1 (Y) and 2 (Z)
        new_affine[:, [1, 2]] = new_affine[:, [2, 1]]
    else:
        return img
    
    new_img = nib.Nifti1Image(new_data, new_affine, header=img.header)
    return new_img

def create_mosaics(nifti_path):
    print(f"Processing: {nifti_path}")
    try:
        img = image.load_img(nifti_path)
    except Exception as e:
        print(f"Error loading {nifti_path}: {e}")
        return

    base_name = os.path.splitext(os.path.basename(nifti_path))[0]
    if base_name.endswith('.nii'):
        base_name = os.path.splitext(base_name)[0]
    
    output_dir = os.path.dirname(nifti_path)
    
    # Number of slices for mosaic
    n_cuts = 36 

    # 1. Axial Mosaic (Z-axis) - No rotation needed
    output_path_z = os.path.join(output_dir, f"{base_name}_mosaic_z.png")
    try:
        print(f"Creating Z mosaic: {output_path_z}")
        display = plotting.plot_anat(img, display_mode='mosaic', cut_coords=n_cuts, title=f"{base_name} Axial (Z)", output_file=output_path_z)
        display.close()
    except Exception as e:
        print(f"Error creating Z mosaic: {e}")

    # 2. Sagittal Mosaic (X-axis) - Rotate X to Z
    output_path_x = os.path.join(output_dir, f"{base_name}_mosaic_x.png")
    try:
        print(f"Creating X mosaic: {output_path_x}")
        img_x = permute_to_z(img, 'x')
        display = plotting.plot_anat(img_x, display_mode='mosaic', cut_coords=n_cuts, title=f"{base_name} Sagittal (X)", output_file=output_path_x)
        display.close()
    except Exception as e:
        print(f"Error creating X mosaic: {e}")

    # 3. Coronal Mosaic (Y-axis) - Rotate Y to Z
    output_path_y = os.path.join(output_dir, f"{base_name}_mosaic_y.png")
    try:
        print(f"Creating Y mosaic: {output_path_y}")
        img_y = permute_to_z(img, 'y')
        display = plotting.plot_anat(img_y, display_mode='mosaic', cut_coords=n_cuts, title=f"{base_name} Coronal (Y)", output_file=output_path_y)
        display.close()
    except Exception as e:
        print(f"Error creating Y mosaic: {e}")


def main():
    root_dir = "/home/ajoshi/Desktop/for_jesus_meeting/"
    if not os.path.exists(root_dir):
        print(f"Directory not found: {root_dir}")
        return

    # Find nifti files recursively
    nifti_files = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.nii') or file.endswith('.nii.gz'):
                nifti_files.append(os.path.join(root, file))
    
    if not nifti_files:
        print("No nifti files found.")
        return

    print(f"Found {len(nifti_files)} nifti files.")

    for nifti_path in nifti_files:
        create_mosaics(nifti_path)

if __name__ == "__main__":
    main()
