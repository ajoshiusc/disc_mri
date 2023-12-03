import os
import numpy as np
import nibabel as nib
from nilearn import surface
import matplotlib.pyplot as plt
from nilearn.plotting import plot_surf_roi
from nilearn.plotting import plot_surf

from nilearn.datasets import fetch_surf_fsaverage, fetch_atlas_surf_destrieux

FREESURFER_SUB = '/deneb_disk/3T_vs_low_field/freesurfer_processed_subjects'

subname = 'subj_4_vol2_3T'
# Set the path to the subject's directory containing the aseg.mgz file
subject_dir = f'/deneb_disk/3T_vs_low_field/freesurfer_processed_subjects/subjects/{subname}'


# Load the fsaverage surface
fsaverage_surface = surface.load_surf_mesh(f'{FREESURFER_SUB}/fsaverage/surf/lh.white')

# Load the fsaverage label
label_file_path = f'{FREESURFER_SUB}/fsaverage/label/lh.aparc.annot'

label_data = nib.freesurfer.read_annot(label_file_path)

# Extract label names and label indices
label_names, label_indices = label_data[2], label_data[0]


avg_thickness = np.zeros(len(label_indices))


# Load the aseg.mgz file containing the cortical thickness data
thickness_file = os.path.join(subject_dir, 'mri', 'aseg.mgz')
thickness_file = os.path.join(subject_dir, 'surf', 'lh.thickness.fwhm20.fsaverage.mgh')
thickness_data = nib.load(thickness_file).get_fdata()


for i in range(1,max(label_indices)+1):
    avg_thickness[label_indices == i] = np.mean(thickness_data[label_indices == i])


f = plot_surf(fsaverage_surface, surf_map=avg_thickness, hemi='left',engine='plotly',cmap='hot', view='lateral', colorbar=True,vmax=3,vmin=0)

f.savefig(f'{subname}_fs_lh_thickness.png')



