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
import matplotlib.pyplot as plt
from scipy.stats import linregress

atlas = "/home/ajoshi/software/BrainSuite23a/svreg/BrainSuiteAtlas1/mri.label.nii.gz"


# Load the NIfTI label file
nifti_file_path = atlas  # Replace with the path to your NIfTI file
label_img = nib.load(nifti_file_path)
label_data = label_img.get_fdata()


# Input array of scalars (assuming it has the same dimensions as the label image)
roi_vols_3t = np.load("brainSuite_3T.npz")["roi_vols"]
roi_vols_lf = np.load("brainSuite_low_field.npz")["roi_vols"]
label_ids = np.load("brainSuite_3T.npz")["label_ids"]


roi_vols_3t = roi_vols_3t[:,:,1:-1]
roi_vols_lf = roi_vols_lf[:,:,0,1:-1]

# for LF dims of roi_vols_lf is session, subj, param, roino
# for 3T dims of roi_vols_3t is session, subj, roino

stat_3t_intra = np.zeros(label_data.shape)

param = 0
roi_vols_3t = np.mean(roi_vols_3t,axis=0).flatten()
roi_vols_lf = np.mean(roi_vols_lf,axis=0).flatten()

import numpy as np
import matplotlib.pyplot as plt

# Sample data for the 1st and 2nd repetitions at 0.55T and 3T
data_0_55T = {
    'First Repetition': [value1, value2, ...],  # Replace with your data
    'Second Repetition': [value1, value2, ...]  # Replace with your data
}

data_3T = {
    'First Repetition': [value1, value2, ...],  # Replace with your data
    'Second Repetition': [value1, value2, ...]  # Replace with your data
}

# Calculate the differences and means for both datasets
diff_0_55T = np.array(data_0_55T['First Repetition']) - np.array(data_0_55T['Second Repetition'])
mean_0_55T = (np.array(data_0_55T['First Repetition']) + np.array(data_0_55T['Second Repetition'])) / 2

diff_3T = np.array(data_3T['First Repetition']) - np.array(data_3T['Second Repetition'])
mean_3T = (np.array(data_3T['First Repetition']) + np.array(data_3T['Second Repetition'])) / 2

# Bland-Altman Plot for 0.55T
plt.figure(figsize=(8, 6))
plt.scatter(mean_0_55T, diff_0_55T, c='blue', marker='o', label='0.55T')
plt.axhline(np.mean(diff_0_55T), color='red', linestyle='--', label='Bias')
plt.axhline(np.mean(diff_0_55T) + 1.96 * np.std(diff_0_55T), color='gray', linestyle='--', label='Upper LoA')
plt.axhline(np.mean(diff_0_55T) - 1.96 * np.std(diff_0_55T), color='gray', linestyle='--', label='Lower LoA')
plt.xlabel('Mean of 1st and 2nd Repetitions')
plt.ylabel('Difference (1st - 2nd Repetition)')
plt.legend()
plt.title('Bland-Altman Plot for 0.55T')
plt.grid(True)

# Bland-Altman Plot for 3T
plt.figure(figsize=(8, 6))
plt.scatter(mean_3T, diff_3T, c='green', marker='s', label='3T')
plt.axhline(np.mean(diff_3T), color='red', linestyle='--', label='Bias')
plt.axhline(np.mean(diff_3T) + 1.96 * np.std(diff_3T), color='gray', linestyle='--', label='Upper LoA')
plt.axhline(np.mean(diff_3T) - 1.96 * np.std(diff_3T), color='gray', linestyle='--', label='Lower LoA')
plt.xlabel('Mean of 1st and 2nd Repetitions')
plt.ylabel('Difference (1st - 2nd Repetition)')
plt.legend()
plt.title('Bland-Altman Plot for 3T')
plt.grid(True)

plt.show()
