#!/usr/bin/env python3
"""
Create WM and GM brain masks from the fetal tissue atlas
"""

import nibabel as nib
import numpy as np

# Load the tissue atlas
fetal_atlas_tissue = "/deneb_disk/disc_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA30_tissue.nii.gz"
tissue_img = nib.load(fetal_atlas_tissue)
tissue_data = tissue_img.get_fdata()

# Define tissue labels based on labelnames.csv and what's actually present in STA30
GM_LABELS = [112, 113]  # Cortical_Plate_L, Cortical_Plate_R

# For GA30, white matter is represented by developmental zones:
# 114, 115: Subplate_L, Subplate_R
# 116, 117: Inter_Zone_L, Inter_Zone_R  
# 118, 119: Vent_Zone_L, Vent_Zone_R
# 122, 123: Internal_Capsule_L, Internal_Capsule_R
WM_LABELS = [114, 115, 116, 117, 118, 119, 122, 123]  # All white matter zones

# Create GM mask
gm_mask = np.isin(tissue_data, GM_LABELS).astype(np.uint8)
print(f"GM mask: {np.sum(gm_mask)} voxels")

# Create WM mask
wm_mask = np.isin(tissue_data, WM_LABELS).astype(np.uint8)
print(f"WM mask: {np.sum(wm_mask)} voxels")

# Save GM mask
gm_mask_img = nib.Nifti1Image(gm_mask, tissue_img.affine, tissue_img.header)
nib.save(gm_mask_img, 'STA30_GM_mask.nii.gz')
print("Saved: STA30_GM_mask.nii.gz")

# Save WM mask
wm_mask_img = nib.Nifti1Image(wm_mask, tissue_img.affine, tissue_img.header)
nib.save(wm_mask_img, 'STA30_WM_mask.nii.gz')
print("Saved: STA30_WM_mask.nii.gz")

# Create combined mask for visualization
combined_mask = np.zeros_like(tissue_data, dtype=np.uint8)
combined_mask[gm_mask == 1] = 1  # GM = 1
combined_mask[wm_mask == 1] = 2  # WM = 2

combined_mask_img = nib.Nifti1Image(combined_mask, tissue_img.affine, tissue_img.header)
nib.save(combined_mask_img, 'STA30_WM_GM_combined_mask.nii.gz')
print("Saved: STA30_WM_GM_combined_mask.nii.gz")

print("\nMask creation complete!")
print("To visualize in FSLeyes:")
print("fsleyes /deneb_disk/disc_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA30.nii.gz STA30_WM_GM_combined_mask.nii.gz &")
