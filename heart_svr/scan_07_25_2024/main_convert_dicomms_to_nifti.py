# This file converts a batch of acquisitions at DISC to nifti files

import dicom2nifti
import glob
import os

# scans_dir = '/deneb_disk/fetal_scan_8_3_2022/data'
scans_dir_top = (
    "/deneb_disk/disc_mri/for_Ye_Heart_07_26_2024/vol0929/vol0929/dicom_recon"
)
stack_dir_all = glob.glob(scans_dir_top + "/*")

for stack_dir in stack_dir_all:

    # stack_id =stack_dir.split('ssfp_')[-1][0:8]
    phase_dir_all = glob.glob(stack_dir + "/*")

    for phase_dir in phase_dir_all:

        phase = phase_dir.split("/")[-1]
        out_dir = "/deneb_disk/disc_mri/for_Ye_Heart_07_26_2024/nifti_files/" + phase

        if not os.path.isdir(out_dir):
            os.mkdir(out_dir)

        s = phase_dir
        print(s)

        dicom2nifti.convert_dir.convert_directory(s, out_dir, compression=True)
        print("Converted", s)
