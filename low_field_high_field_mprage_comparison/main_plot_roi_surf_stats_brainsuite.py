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
from dfsio import readdfs, writedfs
from surfproc import patch_color_attrib, view_patch_vtk
import plotly.graph_objs as go
import plotly.io as pio

atlas_left = (
    "/home/ajoshi/Software/BrainSuite23a/svreg/BrainSuiteAtlas1/mri.left.mid.cortex.dfs"
)
atlas_right = "/home/ajoshi/Software/BrainSuite23a/svreg/BrainSuiteAtlas1/mri.right.mid.cortex.dfs"


atlas_left = readdfs(atlas_left)

label_data_left = atlas_left.labels

atlas_right = readdfs(atlas_right)
label_data_right = atlas_right.labels


# Input array of scalars (assuming it has the same dimensions as the label image)
roi_surf_3t = np.load("brainSuite_3T.npz")["roi_thickness_3t"]
roi_surf_lf = np.load("brainSuite_low_field.npz")["roi_thickness_lf"]
label_ids = np.load("brainSuite_3T.npz")["cortical_label_ids"]

# for LF dims of roi_vols_lf is session, subj, param, roino
# for 3T dims of roi_vols_3t is session, subj, roino

stat_3t_intra_left = np.zeros(label_data_left.shape)
stat_3t_intra_right = np.zeros(label_data_right.shape)

param = 0

for i, idx in enumerate(label_ids):
    stat_3t_intra_left[label_data_left == idx] = np.mean(
        np.std(roi_surf_3t[:, :, i], axis=0)
    )  # - roi_vols_3t[1, :, i]))
    stat_3t_intra_right[label_data_right == idx] = np.mean(
        np.std(roi_surf_3t[:, :, i], axis=0)
    )  # - roi_vols_3t[1, :, i]))


left_stat = patch_color_attrib(atlas_left, values=stat_3t_intra_left, cmap='jet', clim=[0,1])
right_stat = patch_color_attrib(atlas_right, values=stat_3t_intra_right, cmap='jet', clim=[0,1])

writedfs('left_stat_intra_3t.dfs', left_stat)
writedfs('right_stat_intra_3t.dfs', right_stat)

# view_patch(left_stat)

stat_3t_inter_left = np.zeros(label_data_left.shape)
stat_3t_inter_right = np.zeros(label_data_right.shape)

param = 0

for i, idx in enumerate(label_ids):
    stat_3t_inter_left[label_data_left == idx] = np.mean(
        np.std(roi_surf_3t[:, :, i], axis=1)
    )
    stat_3t_inter_right[label_data_right == idx] = np.mean(
        np.std(roi_surf_3t[:, :, i], axis=1)
    )

# Overlay scalar data on top of the ROIs

left_stat = patch_color_attrib(atlas_left, values=stat_3t_inter_left, cmap='jet', clim=[0,1])
right_stat = patch_color_attrib(atlas_right, values=stat_3t_inter_right, cmap='jet', clim=[0,1])

writedfs('left_stat_inter_3t.dfs', left_stat)
writedfs('right_stat_inter_3t.dfs', right_stat)


stat_lf_intra_left = np.zeros(label_data_left.shape)
stat_lf_intra_right = np.zeros(label_data_right.shape)

param = 0
for i, idx in enumerate(label_ids):
    stat_lf_intra_left[label_data_left == idx] = np.mean(
        np.std(roi_surf_lf[:, :, 0, i], axis=0))
    stat_lf_intra_right[label_data_right == idx] = np.mean(
        np.std(roi_surf_lf[:, :, 0, i], axis=0))

    #stat_lf_intra[label_data == idx] = np.mean(np.std(roi_vols_lf[:, :, 0, i], axis=0))

left_stat = patch_color_attrib(atlas_left, values=stat_lf_intra_left, cmap='jet', clim=[0,1])
right_stat = patch_color_attrib(atlas_right, values=stat_lf_intra_right, cmap='jet', clim=[0,1])

writedfs('left_stat_intra_lf.dfs', left_stat)
writedfs('right_stat_intra_lf.dfs', right_stat)

# Overlay scalar data on top of the ROIs
stat_lf_inter_left = np.zeros(label_data_left.shape)
stat_lf_inter_right = np.zeros(label_data_right.shape)

param = 0

for i, idx in enumerate(label_ids):
    stat_lf_inter_left[label_data_left == idx] = np.mean(
        np.std(roi_surf_lf[:, :, 0, i], axis=1))
    stat_lf_inter_right[label_data_right == idx] = np.mean(
        np.std(roi_surf_lf[:, :, 0, i], axis=1))

left_stat = patch_color_attrib(atlas_left, values=stat_lf_inter_left, cmap='jet', clim=[0,1])
right_stat = patch_color_attrib(atlas_right, values=stat_lf_inter_right, cmap='jet', clim=[0,1])

writedfs('left_stat_inter_lf.dfs', left_stat)
writedfs('right_stat_inter_lf.dfs', right_stat)

print("done")
