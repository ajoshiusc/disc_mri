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
import nilearn.image as ni
from scipy.stats import linregress


roi_surf_3t1 = np.load("freesurfer_3T.npz")["left_roi_thickness_3t"]
roi_surf_3t2 = np.load("freesurfer_3T.npz")["right_roi_thickness_3t"]
roi_surf_3t = np.concatenate((roi_surf_3t1, roi_surf_3t2), axis=2)

roi_surf_lf1 = np.load("freesurfer_low_field.npz")["left_roi_thickness_lf"]
roi_surf_lf2 = np.load("freesurfer_low_field.npz")["right_roi_thickness_lf"]
roi_surf_lf = np.concatenate((roi_surf_lf1, roi_surf_lf2), axis=3)


label_ids = np.load("freesurfer_3T.npz")["cortical_label_ids"]

# for LF dims of roi_surf_lf is session, subj, param, roino
# for 3T dims of roi_surf_3t is session, subj, roino


# roi_surf_3t = roi_surf_3t[:,:,:]
roi_surf_lf = roi_surf_lf[:, :, 0, :]


# for LF dims of roi_surf_lf is session, subj, param, roino
# for 3T dims of roi_surf_3t is session, subj, roino


param = 0
surf_3t_avg = np.mean(roi_surf_3t, axis=0).flatten()
surf_lf_avg = np.mean(roi_surf_lf, axis=0).flatten()


x = surf_3t_avg
y = surf_lf_avg
# Calculate correlation coefficient (Pearson's r)
correlation = np.corrcoef(x, y)[0, 1]

# Calculate R-squared value
slope, intercept, r_value, p_value, std_err = linregress(x, y)
r_squared = r_value**2


plt.figure(figsize=(6, 6))


# Create a scatter plot with increased font size
plt.rcParams.update({'font.size': 16})

# Create a scatter plot
plt.scatter(x, y, label=f"R\N{SUPERSCRIPT TWO}: {r_squared:.2f}")
plt.xlim(0, 4)
plt.ylim(0, 4)
# plot the regression line and include the equation in the plot, also include correlation and R-squared values, and p-value
x = np.linspace(0, 4, 100)
plt.plot(
    x, slope * x + intercept, color="red", label=f"y = {slope:.2f}x + {intercept:.2f}"
)

# Add labels and legend
plt.xlabel("3T ROI avg cortical thickness in mm")
plt.ylabel("0.55 ROI avg cortical thickness in mm")
plt.legend()

plt.savefig("3t_vs_lf_roi_avg_cortical_thickness_freesurfer_avg.png")

# Show the plot
plt.show()


roi_surf_3t = roi_surf_3t[0].flatten()
roi_surf_lf = roi_surf_lf[0].flatten()


x = roi_surf_3t
y = roi_surf_lf
# Calculate correlation coefficient (Pearson's r)
correlation = np.corrcoef(x, y)[0, 1]

# Calculate R-squared value
slope, intercept, r_value, p_value, std_err = linregress(x, y)
r_squared = r_value**2

# 


plt.figure(figsize=(6, 6))


# Create a scatter plot with increased font size
plt.rcParams.update({'font.size': 16})

# Create a scatter plot
plt.scatter(x, y, label=f"R\N{SUPERSCRIPT TWO}: {r_squared:.2f}")


plt.xlim(0, 4)
plt.ylim(0, 4)
# plot the regression line and include the equation in the plot, also include correlation and R-squared values, and p-value
x= np.linspace(0, 4, 100)
plt.plot(
    x, slope * x + intercept, color="red", label=f"y = {slope:.2f}x + {intercept:.2f}"
)
# legend should be on top left corner
plt.legend(loc='upper left')

# Add labels and legend
plt.xlabel("3T ROI avg cortical thickness in mm")
plt.ylabel("0.55 ROI avg cortical thickness in mm")

plt.savefig("3t_vs_lf_roi_avg_cortical_thickness_freesurfer_noavg.png")

# Show the plot
plt.show()
