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
roi_vols_3t = np.load('brainSuite_3T.npz')['roi_vols']
roi_vols_lf = np.load('brainSuite_low_field.npz')['roi_vols']
label_ids = np.load('brainSuite_3T.npz')['label_ids']

# for LF dims of roi_vols_lf is session, subj, param, roino 
# for 3T dims of roi_vols_3t is session, subj, roino 

stat = np.zeros(label_data.shape)

param=0
for i, idx in enumerate(label_ids):
    if idx==2000 or idx==0:
        continue
    stat[label_data == idx] = np.linalg.norm(roi_vols_3t[0,:,i]-roi_vols_3t[1,:,i])


# Overlay scalar data on top of the ROIs
plotting.plot_stat_map(
    nib.Nifti1Image(stat, label_img.affine),
    bg_img=nifti_file_path,
    cmap="viridis",
    title="3T",threshold=0,
    colorbar=True,vmax=4000,
)

plt.show()




stat = np.zeros(label_data.shape)

param=0
for i, idx in enumerate(label_ids):
    if idx==2000 or idx==0:
        continue
    stat[label_data == idx] = np.linalg.norm(roi_vols_lf[0,:,0, i]-roi_vols_lf[1,:,0, i])


# Overlay scalar data on top of the ROIs
plotting.plot_stat_map(
    nib.Nifti1Image(stat, label_img.affine),
    bg_img=nifti_file_path,
    cmap="viridis",
    title="0.55T",threshold=0,
    colorbar=True,vmax=4000,
)

plt.show()

print('done')

