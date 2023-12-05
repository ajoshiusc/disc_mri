import os
import glob
from re import sub
from turtle import left
import nibabel as nib
import numpy as np
import SimpleITK as sitk
from tqdm.contrib.itertools import product

from multiprocessing import Pool

import nibabel as nib
import numpy as np
from nilearn.plotting import plot_roi
from nilearn import surface

FREESURFER_SUB = "/deneb_disk/3T_vs_low_field/freesurfer_processed_subjects"

import matplotlib.pyplot as plt
#plt.plot(range(10), range(10))
#plt.show()
import matplotlib
matplotlib.use('TkAgg')

def get_roiwise_thickness(
    left_thickness_file,
    right_thickness_file,
    left_label_data,
    right_label_data,
    cortical_roi_ids,
):
    # Load the left fsaverage surface
    # fsaverage_surf_left = surface.load_surf_mesh(f'{FREESURFER_SUB}/fsaverage/surf/lh.white')

    # Load the right fsaverage surface
    # fsaverage_surf_right = surface.load_surf_mesh(f'{FREESURFER_SUB}/fsaverage/surf/rh.white')

    # Load the left fsaverage label
    # left_label_file_path = f'{FREESURFER_SUB}/fsaverage/label/lh.aparc.annot'
    # left_label_data = nib.freesurfer.read_annot(left_label_file_path)

    # Extract left label names and label indices
    left_label_names, left_label_indices = left_label_data[2], left_label_data[0]

    # Load the right fsaverage label
    # right_label_file_path = f'{FREESURFER_SUB}/fsaverage/label/rh.aparc.annot'
    # right_label_data = nib.freesurfer.read_annot(right_label_file_path)

    # Extract right label names and label indices
    right_label_names, right_label_indices = right_label_data[2], right_label_data[0]

    left_avg_thickness = np.zeros(len(cortical_roi_ids))
    right_avg_thickness = np.zeros(len(cortical_roi_ids))

    left_thickness = nib.load(left_thickness_file).get_fdata()
    right_thickness = nib.load(right_thickness_file).get_fdata()

    for i, r in enumerate(cortical_roi_ids):
        left_avg_thickness[i] = np.mean(left_thickness[left_label_indices == r])
        #print(f"avg cortical thickness for roi {r} is {left_avg_thickness[i]}")

    for i, r in enumerate(cortical_roi_ids):
        right_avg_thickness[i] = np.mean(right_thickness[right_label_indices == r])
        #print(f"avg cortical thickness for roi {r} is {right_avg_thickness[i]}")

    return left_avg_thickness, right_avg_thickness


def get_cortical_thickness(surf_thickness_file):
    return nib.load(surf_thickness_file).get_fdata()[0, 0]


def get_roi_vols(label_file, unique_labels):
    unique_labels = unique_labels.astype(int)
    # Load the NIfTI file
    nifti_img = nib.load(label_file)  # Replace with your NIfTI file path

    # Get the data array from the NIfTI image
    roi_data = nifti_img.get_fdata().astype(int)

    # Get voxel dimensions (voxel size)
    voxel_size = np.prod(nifti_img.header.get_zooms())

    # Get unique ROI labels
    # unique_labels = np.unique(roi_data)

    # Initialize an array to store ROI volumes
    roi_volumes = []

    roi_volumes = np.full(len(unique_labels), np.nan)

    # Compute the volume for each ROI
    for i, label in enumerate(unique_labels):
        roi_volume = np.sum(roi_data == label) * voxel_size
        roi_volumes[i] = roi_volume

    # Print the ROI volumes (label, volume)
    """ for i, volume in enumerate(roi_volumes):
        print(f"ROI {unique_labels[i]}: Volume = {volume} cubic units")
    """
    return roi_volumes


label_ids = np.unique(
    nib.load(
        "/deneb_disk/3T_vs_low_field/freesurfer_processed_subjects/fsaverage/mri/aparc+aseg.mgz"
    )
    .get_fdata()
    .astype(int)
)

label_ids = np.unique(label_ids)


# Load the left fsaverage surface
fsaverage_surf_left = surface.load_surf_mesh(
    f"{FREESURFER_SUB}/fsaverage/surf/lh.white"
)

# Load the right fsaverage surface
fsaverage_surf_right = surface.load_surf_mesh(
    f"{FREESURFER_SUB}/fsaverage/surf/rh.white"
)

# Load the left fsaverage label
left_label_file_path = f"{FREESURFER_SUB}/fsaverage/label/lh.aparc.annot"
left_label_data = nib.freesurfer.read_annot(left_label_file_path)

# Extract left label names and label indices
left_label_names, left_label_indices = left_label_data[2], left_label_data[0]

# Load the right fsaverage label
right_label_file_path = f"{FREESURFER_SUB}/fsaverage/label/rh.aparc.annot"
right_label_data = nib.freesurfer.read_annot(right_label_file_path)

# Extract right label names and label indices
right_label_names, right_label_indices = right_label_data[2], right_label_data[0]

# Get the unique label IDs
cortical_label_ids = np.setdiff1d(
    np.union1d(np.unique(left_label_indices), np.unique(right_label_indices)), (0, -1)
)


nsub = 5
param_list = ("1e-14", "2e-14")
# param = param_list[0]

roi_vols_lf = np.full((2, nsub, 2, len(label_ids)), np.nan)
left_roi_thickness_lf = np.full((2, nsub, 2, len(cortical_label_ids)), np.nan)
right_roi_thickness_lf = np.full((2, nsub, 2, len(cortical_label_ids)), np.nan)

thickness_left_lf = np.full((2, nsub, 2, len(left_label_indices)), np.nan)
thickness_right_lf = np.full((2, nsub, 2, len(right_label_indices)), np.nan)


for sess, n, p in product((1, 2), range(1, nsub + 1), range(2)):
    param = param_list[p]
    out_dir = (
        "/deneb_disk/3T_vs_low_field/freesurfer_processed_subjects/subjects/subj_"
        + str(n)
        + "_vol"
        + str(sess)
        + "_LF_"
        + param
    )

    sub_label_file = out_dir + "/mri/aparc+aseg.mgz"
    anat_img_file = out_dir + "/mri/T1.mgz"

    sub_thickness_left_file = out_dir + "/surf/lh.thickness.fsaverage.mgh"
    sub_thickness_right_file = out_dir + "/surf/rh.thickness.fsaverage.mgh"

    # Add the labels as an overlay
    plot_roi(
        roi_img=sub_label_file,
        bg_img=anat_img_file,
        cmap="Paired",
        alpha=0.5,
        draw_cross=False,
        colorbar=True,
        output_file="subj"
        + str(n)
        + "_vol"
        + str(sess)
        + "_"
        + param
        + "_LF_freesurfer.png",
    )

    if os.path.isfile(sub_label_file):
        roi_vols_lf[sess - 1, n - 1, p, :] = get_roi_vols(sub_label_file, label_ids)
        thickness_left_lf[sess - 1, n - 1, p, :] = get_cortical_thickness(
            sub_thickness_left_file
        )
        thickness_right_lf[sess - 1, n - 1, p, :] = get_cortical_thickness(
            sub_thickness_right_file
        )

        (
            left_roi_thickness_lf[sess - 1, n - 1, p, :],
            right_roi_thickness_lf[sess - 1, n - 1, p, :],
        ) = get_roiwise_thickness(
            sub_thickness_left_file,
            sub_thickness_right_file,
            left_label_data,
            right_label_data,
            cortical_label_ids,
        )

    else:
        print(
            f"The following label file does not exist!! {sub_label_file} Skipping...:"
        )

np.savez(
    "freesurfer_low_field.npz",
    roi_vols=roi_vols_lf,
    nsub=nsub,
    param_list=param_list,
    label_ids=label_ids,
    left_roi_thickness_lf=left_roi_thickness_lf,
    right_roi_thickness_lf=right_roi_thickness_lf,
    thickness_left_lf=thickness_left_lf,
    thickness_right_lf=thickness_right_lf,
    cortical_label_ids=cortical_label_ids,
)

print("Done! for LF")


roi_vols_3t = np.full((2, nsub, len(label_ids)), np.nan)
left_roi_thickness_3t = np.full((2, nsub, len(cortical_label_ids)), np.nan)
right_roi_thickness_3t = np.full((2, nsub, len(cortical_label_ids)), np.nan)

thickness_left_3t = np.full((2, nsub, len(left_label_indices)), np.nan)
thickness_right_3t = np.full((2, nsub, len(right_label_indices)), np.nan)


for sess, n in product((1, 2), range(1, nsub + 1)):
    out_dir = (
        "/deneb_disk/3T_vs_low_field/freesurfer_processed_subjects/subjects/subj_"
        + str(n)
        + "_vol"
        + str(sess)
        + "_3T"
    )

    sub_label_file = out_dir + "/mri/aparc+aseg.mgz"
    anat_img_file = out_dir + "/mri/T1.mgz"
    sub_thickness_left_file = out_dir + "/surf/lh.thickness.fsaverage.mgh"
    sub_thickness_right_file = out_dir + "/surf/rh.thickness.fsaverage.mgh"

    # Add the labels as an overlay
    plot_roi(
        roi_img=sub_label_file,
        bg_img=anat_img_file,
        cmap="Paired",
        alpha=0.5,
        draw_cross=False,
        colorbar=True,
        output_file="subj" + str(n) + "_vol" + str(sess) + "_3T_freesurfer.png",
    )

    if os.path.isfile(sub_label_file):
        roi_vols_3t[sess - 1, n - 1, :] = get_roi_vols(sub_label_file, label_ids)
        thickness_left_3t[sess - 1, n - 1, :] = get_cortical_thickness(
            sub_thickness_left_file
        )

        thickness_right_3t[sess - 1, n - 1, :] = get_cortical_thickness(
            sub_thickness_right_file
        )

        (left_roi_thickness_3t[sess - 1, n - 1, :], right_roi_thickness_3t[sess - 1, n - 1, :]) = get_roiwise_thickness(
            sub_thickness_left_file,
            sub_thickness_right_file,
            left_label_data,
            right_label_data,
            cortical_label_ids,
        )

    else:
        print(
            f"The following label file does not exist!! {sub_label_file} Skipping...:"
        )


np.savez(
    "freesurfer_3T.npz",
    roi_vols=roi_vols_3t,
    nsub=nsub,
    label_ids=label_ids,
    left_roi_thickness_3t=left_roi_thickness_3t,
    right_roi_thickness_3t=right_roi_thickness_3t,
    thickness_left_3t=thickness_left_3t,
    thickness_right_3t=thickness_right_3t,
    cortical_label_ids=cortical_label_ids,
)


print("Done! for 3T")
