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



# Load data
roi_surf_3t = np.load("brainSuite_3T.npz")["roi_thickness_3t"]
roi_surf_lf = np.load("brainSuite_low_field.npz")["roi_thickness_lf"]
label_ids = np.load("brainSuite_3T.npz")["cortical_label_ids"]

# for LF dims of roi_surf_lf is session, subj, param, roino
# for 3T dims of roi_surf_3t is session, subj, roino



#roi_surf_3t = roi_surf_3t[:,:,:]
roi_surf_lf = roi_surf_lf[:,:,0,:]





# for LF dims of roi_surf_lf is session, subj, param, roino
# for 3T dims of roi_surf_3t is session, subj, roino


param = 0
roi_surf_3t_avg = np.mean(roi_surf_3t,axis=0).flatten()
roi_surf_lf_avg = np.mean(roi_surf_lf,axis=0).flatten()


x= roi_surf_3t_avg
y = roi_surf_lf_avg
# Calculate correlation coefficient (Pearson's r)
correlation = np.corrcoef(x, y)[0, 1]

# Calculate R-squared value
slope, intercept, r_value, p_value, std_err = linregress(x, y)
r_squared = r_value ** 2

# Create a scatter plot
plt.scatter(x, y, label=f'Correlation: {correlation:.2f}\nR-squared: {r_squared:.2f}')

# Add labels and legend
plt.xlabel('3T ROI avg cortical thickness')
plt.ylabel('0.55 ROI avg cortical thickness')
plt.legend()

plt.savefig('3t_vs_lf_roi_avg_cortical_thickness_brainsuite_avg.png')

# Show the plot
plt.show()




roi_surf_3t = roi_surf_3t[0].flatten()
roi_surf_lf = roi_surf_lf[0].flatten()


x= roi_surf_3t
y = roi_surf_lf
# Calculate correlation coefficient (Pearson's r)
correlation = np.corrcoef(x, y)[0, 1]

# Calculate R-squared value
slope, intercept, r_value, p_value, std_err = linregress(x, y)
r_squared = r_value ** 2

# Create a scatter plot
plt.scatter(x, y, label=f'Correlation: {correlation:.2f}\nR-squared: {r_squared:.2f}')

# Add labels and legend
plt.xlabel('3T ROI avg cortical thickness')
plt.ylabel('0.55 ROI avg cortical thickness')
plt.legend()

plt.savefig('3t_vs_lf_roi_avg_cortical_thickness_brainsuite_noavg.png')

# Show the plot
plt.show()