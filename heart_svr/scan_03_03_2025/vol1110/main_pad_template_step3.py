import nibabel as nib
from nilearn.image import new_img_like
import numpy as np

import nibabel as nib
import numpy as np
import nibabel as nib
import numpy as np


def pad_nifti(input_file, output_file, pad_width):
    # Load the NIfTI file
    nifti_img = nib.load(input_file)
    data = nifti_img.get_fdata()
    affine = nifti_img.affine

    # Pad the data
    padded_data = np.pad(data, pad_width=((pad_width, pad_width),
                                          (pad_width, pad_width),
                                          (pad_width, pad_width)),
                         mode='constant', constant_values=0)

    # Calculate voxel sizes
    voxel_sizes = np.sqrt((affine[:3, :3] ** 2).sum(axis=0))

    # Adjust the affine matrix for the new origin
    new_affine = affine.copy()
    
    translation_adjustment = np.eye(4)
    translation_adjustment[:3, 3] = -pad_width #* voxel_sizes
    new_affine = new_affine @ translation_adjustment

    # Create a new NIfTI image
    padded_img = nib.Nifti1Image(padded_data, affine=new_affine)

    # Save the padded NIfTI file
    nib.save(padded_img, output_file)




# Define the path to the template and mask images
template = "/deneb_disk/disc_mri/disc_mri/heart_svr_acquisition_03_03_2025/vol1110_template/p59_cardiac_svr_sweep_1_res_15.nii.gz"
mask = "/deneb_disk/disc_mri/disc_mri/heart_svr_acquisition_03_03_2025/vol1110_template/p59_cardiac_svr_sweep_1_res_15.mask.nii.gz"

padded_template_filename = "/deneb_disk/disc_mri/disc_mri/heart_svr_acquisition_03_03_2025/vol1110_template/p59_cardiac_svr_sweep_1_res_15.pad.nii.gz"
padded_mask_filename = "/deneb_disk/disc_mri/disc_mri/heart_svr_acquisition_03_03_2025/vol1110_template/p59_cardiac_svr_sweep_1_res_15.pad.mask.nii.gz"

pad_width = 20

# Example usage
input_file = template
output_file = padded_template_filename

pad_nifti(input_file, output_file, pad_width)

# Example usage
input_file = mask
output_file = padded_mask_filename

pad_nifti(input_file, output_file, pad_width)

