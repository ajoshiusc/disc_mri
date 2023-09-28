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
label_ids = np.load('brainSuite_3T.npz')['label_ids']


stat = np.zeros(label_data.shape)

for i, idx in enumerate(label_ids):
    stat[label_data == idx] = roi_vols_3t[i]

# Create a color-coded plot of ROIs using Nilearn
plotting.plot_roi(
    label_img, bg_img=None, cmap="Paired", title="Color-coded ROIs", colorbar=True
)
plotting.plot_stat_map(
    label_img, bg_img=None, cut_coords=None, display_mode="z", alpha=0.7, colorbar=True
)

# Overlay scalar data on top of the ROIs
plotting.plot_stat_map(
    nib.Nifti1Image(stat, label_img.affine),
    bg_img=None,
    cmap="viridis",
    title="Scalar Overlay",
    colorbar=True,
)

plt.show()
