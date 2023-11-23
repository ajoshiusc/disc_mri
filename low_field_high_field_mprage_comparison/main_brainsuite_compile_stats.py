import os
import glob
import nibabel as nib
import numpy as np
import SimpleITK as sitk
from tqdm.contrib.itertools import product
from dfsio import readdfs, writedfs
from multiprocessing import Pool

import nibabel as nib
import numpy as np
from nilearn.plotting import plot_roi


def get_roiwise_thickness(left_thickness_file, right_thickness_file, roi_list):
    left_label_file = left_thickness_file
    right_label_file = right_thickness_file

    avg_roiwise_thickness = np.zeros(len(roi_list))

    sl = readdfs(left_thickness_file)
    sr = readdfs(right_thickness_file)
    labl = readdfs(left_label_file)
    labr = readdfs(right_label_file)

    for i, r in enumerate(roi_list):
        if np.sum(labl.labels == r) > 0:
            avg_roiwise_thickness[i] = np.mean(sl.attributes[labl.labels == r])
        else:
            avg_roiwise_thickness[i] = np.mean(sr.attributes[labr.labels == r])

        print(f"avg cortical thickness for roi {r} is {avg_roiwise_thickness[i]}")

    return avg_roiwise_thickness


def get_cortical_thickness(surf_file):
    s = readdfs(surf_file)

    return s.attributes


def get_roi_vols(label_file, unique_labels):
    unique_labels = unique_labels.astype(int)
    # Load the NIfTI file
    nifti_img = nib.load(label_file)  # Replace with your NIfTI file path

    # Get the data array from the NIfTI image
    sub_lab_data = nifti_img.get_fdata().astype(int)
    roi_data = np.mod(sub_lab_data, 1000)
    roi_data[sub_lab_data == 2000] = 2000

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

    return roi_volumes


label_ids = np.unique(
    nib.load(
        "/home/ajoshi/Software/BrainSuite23a/svreg/BrainSuiteAtlas1/mri.label.nii.gz"
    ).get_fdata()
)


left_surf = readdfs(
    "/home/ajoshi/Software/BrainSuite23a/svreg/BrainSuiteAtlas1/mri.left.mid.cortex.dfs"
)


right_surf = readdfs(
    "/home/ajoshi/Software/BrainSuite23a/svreg/BrainSuiteAtlas1/mri.right.mid.cortex.dfs"
)

cortical_label_ids = np.setdiff1d(
    np.union1d(np.unique(left_surf.labels), np.unique(right_surf.labels)), (0)
)

nsub = 5
param_list = ("1e-14", "2e-14")

roi_vols_lf = np.full((2, nsub, 2, len(label_ids)), np.nan)
roi_thickness_lf = np.full((2, nsub, 2, len(cortical_label_ids)), np.nan)


thickness_left_lf = np.full((2, nsub, 2, len(left_surf.vertices)), np.nan)
thickness_right_lf = np.full((2, nsub, 2, len(right_surf.vertices)), np.nan)


for sess, n, p in product((1, 2), range(1, nsub + 1), range(2)):
    param = param_list[p]
    out_dir = (
        "/deneb_disk/3T_vs_low_field/justins_recons/low_field_mprage_data_BrainSuite_4bfc/subj"
        + str(n)
        + "_vol"
        + str(sess)
        + "/"
        + param
    )

    sub_label_file = out_dir + "/T1.svreg.label.nii.gz"
    anat_img_file = out_dir + "/T1.nii.gz"
    sub_thickness_left_file = out_dir + "/atlas.pvc-thickness_0-6mm.left.mid.cortex.dfs"
    sub_thickness_right_file = (
        out_dir + "/atlas.pvc-thickness_0-6mm.right.mid.cortex.dfs"
    )

    # Add the labels as an overlay
    plot_roi(
        roi_img=sub_label_file,
        bg_img=anat_img_file,
        cmap="Paired",
        alpha=0.5,
        draw_cross=False,
        colorbar=False,
        output_file="subj"
        + str(n)
        + "_vol"
        + str(sess)
        + "_"
        + param
        + "_LF_brainsuite.png",
    )

    if os.path.isfile(sub_label_file):
        roi_vols_lf[sess - 1, n - 1, p, :] = get_roi_vols(sub_label_file, label_ids)
        thickness_left_lf[sess - 1, n - 1, p, :] = get_cortical_thickness(
            sub_thickness_left_file
        )
        thickness_right_lf[sess - 1, n - 1, p, :] = get_cortical_thickness(
            sub_thickness_right_file
        )

        roi_thickness_lf[sess - 1, n - 1, p, :] = get_roiwise_thickness(
            sub_thickness_left_file, sub_thickness_right_file, cortical_label_ids
        )

    else:
        print(
            f"The following label file does not exist!! {sub_label_file} Skipping...:"
        )

np.savez(
    "brainSuite_low_field.npz",
    roi_vols=roi_vols_lf,
    thickness_left=thickness_left_lf,
    thickness_right=thickness_right_lf,
    nsub=nsub,
    param_list=param_list,
    label_ids=label_ids,
    roi_thickness_lf=roi_thickness_lf,
    cortical_label_ids = cortical_label_ids,
)

print("Done! for LF")


roi_vols_3t = np.full((2, nsub, len(label_ids)), np.nan)
roi_thickness_3t = np.full((2, nsub, len(cortical_label_ids)), np.nan)

thickness_left_3t = np.full((2, nsub, len(left_surf.vertices)), np.nan)
thickness_right_3t = np.full((2, nsub, len(right_surf.vertices)), np.nan)

for sess, n in product((1, 2), range(1, nsub + 1)):
    out_dir = (
        "/deneb_disk/3T_vs_low_field/3T_mprage_data_BrainSuite_4bfc/subj"
        + str(n)
        + "_vol"
        + str(sess)
    )

    sub_label_file = out_dir + "/T1.svreg.label.nii.gz"
    anat_img_file = out_dir + "/T1.nii.gz"
    sub_thickness_left_file = out_dir + "/atlas.pvc-thickness_0-6mm.left.mid.cortex.dfs"
    sub_thickness_right_file = (
        out_dir + "/atlas.pvc-thickness_0-6mm.right.mid.cortex.dfs"
    )

    # Add the labels as an overlay
    plot_roi(
        roi_img=sub_label_file,
        bg_img=anat_img_file,
        cmap="Paired",
        alpha=0.5,
        draw_cross=False,
        colorbar=False,
        output_file="subj" + str(n) + "_vol" + str(sess) + "_3T_brainsuite.png",
    )

    if os.path.isfile(sub_label_file):
        roi_vols_3t[sess - 1, n - 1, :] = get_roi_vols(sub_label_file, label_ids)
        thickness_left_3t[sess - 1, n - 1, :] = get_cortical_thickness(
            sub_thickness_left_file
        )
        thickness_right_3t[sess - 1, n - 1, :] = get_cortical_thickness(
            sub_thickness_right_file
        )

        roi_thickness_3t[sess - 1, n - 1, :] = get_roiwise_thickness(
            sub_thickness_left_file, sub_thickness_right_file, cortical_label_ids
        )

    else:
        print(
            f"The following label file does not exist!! {sub_label_file} Skipping...:"
        )

np.savez(
    "brainSuite_3T.npz",
    roi_vols=roi_vols_3t,
    thickness_left=thickness_left_3t,
    thickness_right=thickness_right_3t,
    nsub=nsub,
    param_list=param_list,
    label_ids=label_ids,
    roi_thickness_3t=roi_thickness_3t,
    cortical_label_ids = cortical_label_ids,
)
print("Done! for 3T")
