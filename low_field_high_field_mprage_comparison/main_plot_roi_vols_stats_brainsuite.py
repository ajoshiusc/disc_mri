import os
import glob
import nibabel as nib
import numpy as np
import SimpleITK as sitk
from itertools import product

from multiprocessing import Pool

import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt
from nilearn import plotting
import nibabel as nib
import numpy as np
import nilearn.image as ni


atlas = "/home/ajoshi/BrainSuite23a/svreg/BrainSuiteAtlas1/mri.label.nii.gz"


# Load the NIfTI label file
nifti_file_path = atlas  # Replace with the path to your NIfTI file
label_img = nib.load(nifti_file_path)
label_data = label_img.get_fdata()


# Input array of scalars (assuming it has the same dimensions as the label image)
roi_vols_3t = np.load("brainSuite_3T.npz")["roi_vols"]
roi_vols_lf = np.load("brainSuite_low_field.npz")["roi_vols"]
label_ids = np.load("brainSuite_3T.npz")["label_ids"]

# for LF dims of roi_vols_lf is session, subj, param, roino
# for 3T dims of roi_vols_3t is session, subj, roino

stat = np.zeros(label_data.shape)

param = 0
for i, idx in enumerate(label_ids):
    if idx == 2000 or idx == 0:
        continue
    stat[label_data == idx] = np.mean(np.std(roi_vols_3t[:, :, i],axis=0)) # - roi_vols_3t[1, :, i]))


# Overlay scalar data on top of the ROIs
plotting.plot_anat(
    nib.Nifti1Image(stat, label_img.affine),
    cmap="hot",
    title="3T Intra-subject std dev",
    vmin=0,
    draw_cross=False,
    colorbar=True,
    cut_coords=(91, 75, 85),
    vmax=2000,
    output_file="3T_Intra_subject_std_dev.png",
)

plt.show()


stat = np.zeros(label_data.shape)

param = 0
for i, idx in enumerate(label_ids):
    if idx == 2000 or idx == 0:
        continue
    stat[label_data == idx] = np.mean(np.std(roi_vols_3t[:,:,i],axis=1))
    #0.5 * (
    #    np.std(roi_vols_3t[0, :, i]) + np.std(roi_vols_3t[1, :, i])
    #)


# Overlay scalar data on top of the ROIs
plotting.plot_anat(
    nib.Nifti1Image(stat, label_img.affine),
    cmap="hot",
    title="3T Inter-subject std dev",
    vmin=0,
    draw_cross=False,
    colorbar=True,
    cut_coords=(91, 75, 85),
    vmax=4000,
    output_file="3T_Inter_subject_std_dev.png",
)

plt.show()


stat = np.zeros(label_data.shape)

param = 0
for i, idx in enumerate(label_ids):
    if idx == 2000 or idx == 0:
        continue
    stat[label_data == idx] = np.mean(np.std(roi_vols_lf[:, :, 0, i],axis=0))



# Overlay scalar data on top of the ROIs
plotting.plot_anat(
    nib.Nifti1Image(stat, label_img.affine),
    cmap="hot",
    title="0.55T Intra-subject std dev",
    vmin=0,
    colorbar=True,
    draw_cross=False,
    vmax=2000,
    cut_coords=(91, 75, 85),
    output_file="0_55T_Intra_subject_std_dev.png",
)

plt.show()


stat = np.zeros(label_data.shape)

param = 0
for i, idx in enumerate(label_ids):
    if idx == 2000 or idx == 0:
        continue
    stat[label_data == idx] = np.mean(np.std(roi_vols_lf[:, :, 0, i],axis=1))


# Overlay scalar data on top of the ROIs
plotting.plot_anat(
    nib.Nifti1Image(stat, label_img.affine),
    cmap="hot",
    title="0.55T Inter-subject std dev",
    vmin=0,
    colorbar=True,
    draw_cross=False,
    vmax=4000,
    cut_coords=(91, 75, 85),
    output_file="0_55T_Inter_subject_std_dev.png",
)

plt.show()


print("done")
