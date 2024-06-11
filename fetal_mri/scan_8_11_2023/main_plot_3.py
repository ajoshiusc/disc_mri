import nibabel as nib
import numpy as np
import imageio
from nilearn.plotting import plot_anat

# Load the NIfTI image
nifti_file = "/deneb_disk/disc_mri/scan_8_11_2023/outsvr/svr_te140_numstacks_12_iter_0_aligned.nii.gz"  # Replace with your input NIfTI file

atlas_file = (
    "/deneb_disk/disc_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA30.nii.gz"
)
nifti_file_masked = "/deneb_disk/disc_mri/scan_8_11_2023/outsvr/svr_te140_numstacks_12_iter_0_aligned_masked.nii.gz"

# Load the NIfTI image, read atlas image, mask the image with the atlas
img = nib.load(nifti_file)
atlas = nib.load(atlas_file)
data = img.get_fdata()
atlas_data = atlas.get_fdata()
data[atlas_data == 0] = 0
img = nib.Nifti1Image(data, img.affine, img.header)
nib.save(img, nifti_file_masked)


plot_anat(
    nifti_file_masked,
    display_mode="ortho",
    vmin=0,
    vmax=1200,
    cut_coords=(0, 0, 0),
    output_file="svr_te140_numstacks_12_iter_0_aligned_masked.png",
    draw_cross=False,
)
