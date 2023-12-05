import os
import glob
from xml.etree.ElementTree import TreeBuilder
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
from nilearn.plotting import plot_surf, view_surf,plot_surf_stat_map
from nilearn import surface

from test_fs import FREESURFER_SUB

my_cmap = "hot"

FREESURFER_SUB = "/deneb_disk/3T_vs_low_field/freesurfer_processed_subjects"

class atlas_left:
    pass

class atlas_right:
    pass

# Load the left fsaverage surface
atlas_left_fs = surface.load_surf_mesh(f'{FREESURFER_SUB}/fsaverage/surf/lh.white')
atlas_left.vertices = atlas_left_fs.coordinates
atlas_left.faces = atlas_left_fs.faces

# Load the right fsaverage surface
atlas_right_fs = surface.load_surf_mesh(f'{FREESURFER_SUB}/fsaverage/surf/rh.white')
atlas_right.vertices = atlas_right_fs.coordinates
atlas_right.faces = atlas_right_fs.faces

# Load the left fsaverage label
left_label_file_path = f'{FREESURFER_SUB}/fsaverage/label/lh.aparc.annot'
label_data_left = nib.freesurfer.read_annot(left_label_file_path)[0]

right_label_file_path = f'{FREESURFER_SUB}/fsaverage/label/rh.aparc.annot'
label_data_right = nib.freesurfer.read_annot(right_label_file_path)[0]

#label_data_left = atlas_left.labels

#atlas_right = readdfs(atlas_right)
#label_data_right = atlas_right.labels


# Input array of scalars (assuming it has the same dimensions as the label image)
left_roi_surf_3t = np.load("freesurfer_3T.npz")["left_roi_thickness_3t"]
right_roi_surf_3t = np.load("freesurfer_3T.npz")["right_roi_thickness_3t"]
left_roi_surf_lf = np.load("freesurfer_low_field.npz")["left_roi_thickness_lf"]
right_roi_surf_lf = np.load("freesurfer_low_field.npz")["right_roi_thickness_lf"]

label_ids = np.load("freesurfer_3T.npz")["cortical_label_ids"]


# for LF dims of roi_vols_lf is session, subj, param, roino
# for 3T dims of roi_vols_3t is session, subj, roino

stat_3t_intra_left = np.zeros(label_data_left.shape)
stat_3t_intra_right = np.zeros(label_data_right.shape)

param = 0

for i, idx in enumerate(label_ids):
    stat_3t_intra_left[label_data_left == idx] = np.mean(
        np.std(left_roi_surf_3t[:, :, i], axis=0)
    )  # - roi_vols_3t[1, :, i]))
    stat_3t_intra_right[label_data_right == idx] = np.mean(
        np.std(right_roi_surf_3t[:, :, i], axis=0)
    )  # - roi_vols_3t[1, :, i]))


# Overlay scalar data on top of the ROIs
left_stat = patch_color_attrib(atlas_left, values=stat_3t_intra_left, cmap=my_cmap, clim=[0,1])
right_stat = patch_color_attrib(atlas_right, values=stat_3t_intra_right, cmap=my_cmap, clim=[0,1])

writedfs('left_stat_intra_3t_freesurfer.dfs', left_stat)
writedfs('right_stat_intra_3t_freesurfer.dfs', right_stat)

# Save pngs of the left and right hemispheres for the intra-subject 3T stats
f=plot_surf([left_stat.vertices, left_stat.faces],surf_map=stat_3t_intra_left, engine='plotly', colorbar=False,hemi='left', cmap=my_cmap, vmin=0, vmax=.5,view='lateral',symmetric_cmap=False)
f.savefig('left_stat_intra_3t_1_freesurfer.png')
f=plot_surf([left_stat.vertices, left_stat.faces],surf_map=stat_3t_intra_left, engine='plotly', colorbar=False,hemi='left', cmap=my_cmap, vmin=0, vmax=.5,view='medial',symmetric_cmap=False)
f.savefig('left_stat_intra_3t_2_freesurfer.png')

f=plot_surf([right_stat.vertices, right_stat.faces],surf_map=stat_3t_intra_right, engine='plotly', colorbar=False,hemi='right', cmap=my_cmap, vmin=0, vmax=.5,view='lateral',symmetric_cmap=False)
f.savefig('right_stat_intra_3t_1_freesurfer.png')
f=plot_surf([right_stat.vertices, right_stat.faces],surf_map=stat_3t_intra_right, engine='plotly', colorbar=False,hemi='right', cmap=my_cmap, vmin=0, vmax=.5,view='medial',symmetric_cmap=False)
f.savefig('right_stat_intra_3t_2_freesurfer.png')


stat_3t_inter_left = np.zeros(label_data_left.shape)
stat_3t_inter_right = np.zeros(label_data_right.shape)

param = 0

for i, idx in enumerate(label_ids):
    stat_3t_inter_left[label_data_left == idx] = np.mean(
        np.std(left_roi_surf_3t[:, :, i], axis=1)
    )
    stat_3t_inter_right[label_data_right == idx] = np.mean(
        np.std(right_roi_surf_3t[:, :, i], axis=1)
    )

# Overlay scalar data on top of the ROIs

left_stat = patch_color_attrib(atlas_left, values=stat_3t_inter_left, cmap=my_cmap, clim=[0,1])
right_stat = patch_color_attrib(atlas_right, values=stat_3t_inter_right, cmap=my_cmap, clim=[0,1])

writedfs('left_stat_inter_3t_freesurfer.dfs', left_stat)
writedfs('right_stat_inter_3t_freesurfer.dfs', right_stat)

f=plot_surf([left_stat.vertices, left_stat.faces],surf_map=stat_3t_inter_left, engine='plotly', colorbar=False,hemi='left', cmap=my_cmap, vmin=0, vmax=.5,view='lateral',symmetric_cmap=False)
f.savefig('left_stat_inter_3t_1_freesurfer.png')
f=plot_surf([left_stat.vertices, left_stat.faces],surf_map=stat_3t_inter_left, engine='plotly', colorbar=False,hemi='left', cmap=my_cmap, vmin=0, vmax=.5,view='medial',symmetric_cmap=False)
f.savefig('left_stat_inter_3t_2_freesurfer.png')

f=plot_surf([right_stat.vertices, right_stat.faces],surf_map=stat_3t_inter_right, engine='plotly', colorbar=False,hemi='right', cmap=my_cmap, vmin=0, vmax=.5,view='lateral',symmetric_cmap=False)
f.savefig('right_stat_inter_3t_1_freesurfer.png')
f=plot_surf([right_stat.vertices, right_stat.faces],surf_map=stat_3t_inter_right, engine='plotly', colorbar=False,hemi='right', cmap=my_cmap, vmin=0, vmax=.5,view='medial',symmetric_cmap=False)
f.savefig('right_stat_inter_3t_2_freesurfer.png')


stat_lf_intra_left = np.zeros(label_data_left.shape)
stat_lf_intra_right = np.zeros(label_data_right.shape)

param = 0
for i, idx in enumerate(label_ids):
    stat_lf_intra_left[label_data_left == idx] = np.mean(
        np.std(left_roi_surf_lf[:, :, 0, i], axis=0))
    stat_lf_intra_right[label_data_right == idx] = np.mean(
        np.std(right_roi_surf_lf[:, :, 0, i], axis=0))

    #stat_lf_intra[label_data == idx] = np.mean(np.std(roi_vols_lf[:, :, 0, i], axis=0))

left_stat = patch_color_attrib(atlas_left, values=stat_lf_intra_left, cmap=my_cmap, clim=[0,.5])
right_stat = patch_color_attrib(atlas_right, values=stat_lf_intra_right, cmap=my_cmap, clim=[0,.5])

writedfs('left_stat_intra_lf_freesurfer.dfs', left_stat)
writedfs('right_stat_intra_lf_freesurfer.dfs', right_stat)

f=plot_surf([left_stat.vertices, left_stat.faces],surf_map=stat_lf_intra_left, engine='plotly', colorbar=False,hemi='left', cmap=my_cmap, vmin=0, vmax=.5,view='lateral',symmetric_cmap=False)
f.savefig('left_stat_intra_lf_1_freesurfer.png')
f=plot_surf([left_stat.vertices, left_stat.faces],surf_map=stat_lf_intra_left, engine='plotly', colorbar=False,hemi='left', cmap=my_cmap, vmin=0, vmax=.5,view='medial',symmetric_cmap=False)
f.savefig('left_stat_intra_lf_2_freesurfer.png')

f=plot_surf([right_stat.vertices, right_stat.faces],surf_map=stat_lf_intra_right, engine='plotly', colorbar=False,hemi='right', cmap=my_cmap, vmin=0, vmax=.5,view='lateral',symmetric_cmap=False)
f.savefig('right_stat_intra_lf_1_freesurfer.png')
f=plot_surf([right_stat.vertices, right_stat.faces],surf_map=stat_lf_intra_right, engine='plotly', colorbar=False,hemi='right', cmap=my_cmap, vmin=0, vmax=.5,view='medial',symmetric_cmap=False)
f.savefig('right_stat_intra_lf_2_freesurfer.png')



# Overlay scalar data on top of the ROIs
stat_lf_inter_left = np.zeros(label_data_left.shape)
stat_lf_inter_right = np.zeros(label_data_right.shape)

param = 0

for i, idx in enumerate(label_ids):
    stat_lf_inter_left[label_data_left == idx] = np.mean(
        np.std(left_roi_surf_lf[:, :, 0, i], axis=1))
    stat_lf_inter_right[label_data_right == idx] = np.mean(
        np.std(right_roi_surf_lf[:, :, 0, i], axis=1))

left_stat = patch_color_attrib(atlas_left, values=stat_lf_inter_left, cmap=my_cmap, clim=[0,.5])
right_stat = patch_color_attrib(atlas_right, values=stat_lf_inter_right, cmap=my_cmap, clim=[0,.5])

writedfs('left_stat_inter_lf_freesurfer.dfs', left_stat)
writedfs('right_stat_inter_lf_freesurfer.dfs', right_stat)

f=plot_surf([left_stat.vertices, left_stat.faces],surf_map=stat_lf_inter_left, engine='plotly', colorbar=False,hemi='left', cmap=my_cmap, vmin=0, vmax=.5,view='lateral',symmetric_cmap=False)
f.savefig('left_stat_inter_lf_1_freesurfer.png')
f=plot_surf([left_stat.vertices, left_stat.faces],surf_map=stat_lf_inter_left, engine='plotly', colorbar=False,hemi='left', cmap=my_cmap, vmin=0, vmax=.5,view='medial',symmetric_cmap=False)
f.savefig('left_stat_inter_lf_2_freesurfer.png')

f=plot_surf([right_stat.vertices, right_stat.faces],surf_map=stat_lf_inter_right, engine='plotly', colorbar=False,hemi='right', cmap=my_cmap, vmin=0, vmax=.5,view='lateral',symmetric_cmap=False)
f.savefig('right_stat_inter_lf_1_freesurfer.png')
f=plot_surf([right_stat.vertices, right_stat.faces],surf_map=stat_lf_inter_right, engine='plotly', colorbar=False,hemi='right', cmap=my_cmap, vmin=0, vmax=.5,view='medial',symmetric_cmap=False)
f.savefig('right_stat_inter_lf_2_freesurfer.png')



## Plot ratio of inter to intra subject variability for 3T and LF

ratio_3t_left = np.divide(stat_3t_inter_left, stat_3t_intra_left + 1e-6)
ratio_3t_right = np.divide(stat_3t_inter_right, stat_3t_intra_right + 1e-6)

left_stat = patch_color_attrib(atlas_left, values=ratio_3t_left, cmap=my_cmap, clim=[0,10])
right_stat = patch_color_attrib(atlas_right, values=ratio_3t_right, cmap=my_cmap, clim=[0,10])

writedfs('left_ratio_3t_freesurfer.dfs', left_stat)
writedfs('right_ratio_3t_freesurfer.dfs', right_stat)

f=plot_surf([left_stat.vertices, left_stat.faces],surf_map=ratio_3t_left, engine='plotly', colorbar=False,hemi='left', cmap=my_cmap, vmin=0, vmax=10,view='lateral',symmetric_cmap=False)
f.savefig('left_ratio_3t_1_freesurfer.png')
f=plot_surf([left_stat.vertices, left_stat.faces],surf_map=ratio_3t_left, engine='plotly', colorbar=False,hemi='left', cmap=my_cmap, vmin=0, vmax=10,view='medial',symmetric_cmap=False)
f.savefig('left_ratio_3t_2_freesurfer.png')

f=plot_surf([right_stat.vertices, right_stat.faces],surf_map=ratio_3t_right, engine='plotly', colorbar=False,hemi='right', cmap=my_cmap, vmin=0, vmax=10,view='lateral',symmetric_cmap=False)
f.savefig('right_ratio_3t_1_freesurfer.png')
f=plot_surf([right_stat.vertices, right_stat.faces],surf_map=ratio_3t_right, engine='plotly', colorbar=False,hemi='right', cmap=my_cmap, vmin=0, vmax=10,view='medial',symmetric_cmap=False)
f.savefig('right_ratio_3t_2_freesurfer.png')


ratio_lf_left = np.divide(stat_lf_inter_left, stat_lf_intra_left + 1e-6)
ratio_lf_right = np.divide(stat_lf_inter_right, stat_lf_intra_right + 1e-6)

left_stat = patch_color_attrib(atlas_left, values=ratio_lf_left, cmap=my_cmap, clim=[0,10])
right_stat = patch_color_attrib(atlas_right, values=ratio_lf_right, cmap=my_cmap, clim=[0,10])

writedfs('left_ratio_lf_freesurfer.dfs', left_stat)
writedfs('right_ratio_lf_freesurfer.dfs', right_stat)

f=plot_surf([left_stat.vertices, left_stat.faces],surf_map=ratio_lf_left, engine='plotly', colorbar=False,hemi='left', cmap=my_cmap, vmin=0, vmax=10,view='lateral',symmetric_cmap=False)
f.savefig('left_ratio_lf_1_freesurfer.png')
f=plot_surf([left_stat.vertices, left_stat.faces],surf_map=ratio_lf_left, engine='plotly', colorbar=False,hemi='left', cmap=my_cmap, vmin=0, vmax=10,view='medial',symmetric_cmap=False)
f.savefig('left_ratio_lf_2_freesurfer.png')

f=plot_surf([right_stat.vertices, right_stat.faces],surf_map=ratio_lf_right, engine='plotly', colorbar=False,hemi='right', cmap=my_cmap, vmin=0, vmax=10,view='lateral',symmetric_cmap=False)
f.savefig('right_ratio_lf_1_freesurfer.png')
f=plot_surf([right_stat.vertices, right_stat.faces],surf_map=ratio_lf_right, engine='plotly', colorbar=False,hemi='right', cmap=my_cmap, vmin=0, vmax=10,view='medial',symmetric_cmap=False)
f.savefig('right_ratio_lf_2_freesurfer.png')



print("done")
