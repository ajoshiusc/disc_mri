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


x= roi_vols_3t
y = roi_vols_lf
# Calculate correlation coefficient (Pearson's r)
correlation = np.corrcoef(x, y)[0, 1]

# Calculate R-squared value
slope, intercept, r_value, p_value, std_err = linregress(x, y)
r_squared = r_value ** 2

# Create a scatter plot
plt.scatter(x, y, label=f'Correlation: {correlation:.2f}\nR-squared: {r_squared:.2f}')

# Add labels and legend
plt.xlabel('3T ROI volume')
plt.ylabel('0.55 ROI volume')
plt.legend()

plt.savefig('3t_vs_lf_roi_vols.png')

# Show the plot
plt.show()
