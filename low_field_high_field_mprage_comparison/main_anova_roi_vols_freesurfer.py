#||AUM||
#||Shree Ganeshaya Namah||

import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt

# Define the path to the freesurfer Atlas
#atlas = "/home/ajoshi/Software/freesurfer23a/svreg/freesurferAtlas1/mri.label.nii.gz"

# Load the NIfTI label file
#nifti_file_path = atlas
#label_img = nib.load(nifti_file_path)
#label_data = label_img.get_fdata()

# Load input data
roi_vols_3t = np.load("freesurfer_3T.npz")["roi_vols"]
roi_vols_lf = np.load("freesurfer_low_field.npz")["roi_vols"]
label_ids = np.load("freesurfer_3T.npz")["label_ids"]

# Remove unnecessary dimensions from roi_vols_lf, and remove 0 and 2000 
roi_vols_lf = roi_vols_lf[:, :, 0, 1:-1]

# remove 0 and 2000 rois from 3t data
roi_vols_3t = roi_vols_3t[:, :, 1:-1]

# Arrange this data into a 4D array with the dimensions: # repetitions x # ROIs x # subjects x # scanners
roi_vols = np.concatenate((roi_vols_3t, roi_vols_lf), axis=2)
roi_vols = np.moveaxis(roi_vols, 2, 0)
roi_vols = np.moveaxis(roi_vols, 2, 1)

# Do anova analysis to split variance into subject, scanner and roi
import statsmodels.api as sm
from statsmodels.formula.api import ols

# Reshape roi_vols arrays
roi_vols = roi_vols.reshape(2, -1)
roi_vols_3t = roi_vols_3t.reshape(2, -1)
roi_vols_lf = roi_vols_lf.reshape(2, -1)

# Sample data for the 1st and 2nd repetitions at 0.55T and 3T
data_0_55T = {
    "First Repetition": roi_vols_lf[0],
    "Second Repetition": roi_vols_lf[1],
}

data_3T = {
    "First Repetition": roi_vols_3t[0],
    "Second Repetition": roi_vols_3t[1],
}


# add an axis for scanner
roi_vols_3t = roi_vols_3t[:, :, np.newaxis]
roi_vols_lf = roi_vols_lf[:, :, np.newaxis]

# Do the ANOVA
data = np.concatenate((roi_vols_3t, roi_vols_lf), axis=2)
data = data.T

# data is a 3d matrix with dimensions: # subjects x # rois x # scanners. Convert it to a 2d matrix with columns: roi_vols, scanner, subject
data = data.reshape(-1, 3)
data = np.concatenate((data, np.tile(np.arange(2), data.shape[0] // 2)[:, np.newaxis]), axis=1)

# Convert the data to a pandas dataframe
import pandas as pd
df = pd.DataFrame(data, columns=["roi_vols", "scanner", "subject"])
model = ols("roi_vols ~ C(scanner) + C(subject)", data=df).fit()
anova_table = sm.stats.anova_lm(model, typ=2)
print(anova_table)

