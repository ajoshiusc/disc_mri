
import os
import glob
import numpy as np
import nibabel as nib
from nilearn import plotting, image
import matplotlib
import sys

# Force non-interactive backend
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Force output buffering off
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

def create_ortho_views(nifti_path):
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
    
    # Calculate image bounds or center to determine good cut coordinates
    # We want 3 different views: 
    # 1. Center
    # 2. Offset 1 (e.g. +25% of FOV)
    # 3. Offset 2 (e.g. -25% of FOV)
    
    # Get affine and shape
    affine = img.affine
    shape = img.shape
    
    # Calculate FOV in mm
    # Center in voxel coordinates
    center_vox = np.array(shape[:3]) / 2.0
    
    # Offsets in voxels (approx 1/4 of dimension)
    offset_vox = np.array(shape[:3]) / 4.0
    
    # Define 3 coordinates in voxel space
    coords_vox_list = [
        center_vox,                 # Center
        center_vox + offset_vox,    # +offset
        center_vox - offset_vox     # -offset
    ]
    
    # Convert to MNI/World coordinates using affine
    coords_mm_list = []
    for c_vox in coords_vox_list:
        # Apply affine: coord_mm = affine * [x, y, z, 1]
        c_mm = nib.affines.apply_affine(affine, c_vox)
        coords_mm_list.append(c_mm)

    labels = ["center", "offset_pos", "offset_neg"]

    for i, coords in enumerate(coords_mm_list):
        label = labels[i]
        output_filename = f"{base_name}_ortho_{label}.png"
        output_path = os.path.join(output_dir, output_filename)
        
        try:
            print(f"Creating ortho view {label}: {output_path}")
            # display_mode='ortho' shows 3 cuts (Axial, Coronal, Sagittal) intersecting at cut_coords
            display = plotting.plot_anat(
                img, 
                display_mode='ortho', 
                cut_coords=coords, 
                title=f"{base_name} ({label})",
                output_file=output_path
            )
            if display is not None:
                display.close()
        except Exception as e:
            print(f"Error creating ortho view {label} for {nifti_path}: {e}")


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
        create_ortho_views(nifti_path)

if __name__ == "__main__":
    main()
