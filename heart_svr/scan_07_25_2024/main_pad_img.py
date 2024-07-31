import nibabel as nib
from nilearn.image import new_img_like
import numpy as np

# Define the path to the template and mask images
template = "/deneb_disk/disc_mri/for_Ye_Heart_07_26_2024/nifti_files/common_template_mask/p66_cardiac_multi_slice_multi_res_real_time_spiral_ssfp_ga.nii.gz"
mask = "/deneb_disk/disc_mri/for_Ye_Heart_07_26_2024/nifti_files/common_template_mask/p66_cardiac_multi_slice_multi_res_real_time_spiral_ssfp_ga.mask.nii.gz"

padded_template_filename = "/deneb_disk/disc_mri/for_Ye_Heart_07_26_2024/nifti_files/common_template_mask/p66_cardiac_multi_slice_multi_res_real_time_spiral_ssfp_ga_pad.nii.gz"
padded_mask_filename = "/deneb_disk/disc_mri/for_Ye_Heart_07_26_2024/nifti_files/common_template_mask/p66_cardiac_multi_slice_multi_res_real_time_spiral_ssfp_ga.mask_pad.nii.gz"


def pad_nifti_image(img, pad_size):
    """Pads a NIfTI image by the specified amount in all directions.

    Args:
      img: The input NIfTI image.
      pad_size: The amount of padding to add.

    Returns:
      The padded NIfTI image.
    """

    data = img.get_fdata()
    shape = data.shape

    new_shape = (
        shape[0] + pad_size * 2,
        shape[1] + pad_size * 2,
        shape[2] + pad_size * 2,
    )
    padded_data = np.zeros(new_shape, dtype=data.dtype)

    # Calculate slicing indices
    slicing = tuple(slice(pad_size, pad_size + s) for s in shape)
    padded_data[slicing] = data

    padded_img = new_img_like(img, padded_data)
    return padded_img


# Load your NIfTI images
template_img = nib.load(template)
mask_img = nib.load(mask)

# Pad the images
pad_size = 20
padded_template = pad_nifti_image(template_img, pad_size)
padded_mask = pad_nifti_image(mask_img, pad_size)

# Save the padded images (optional)
nib.save(padded_template, padded_template_filename)
nib.save(padded_mask, padded_mask_filename)


# End of main_pad_img.py
