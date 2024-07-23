# This file converts a batch of acquisitions at DISC to nifti files

import dicom2nifti
import glob
import os

all_scans = '/deneb_disk/disc_mri/for_Ye_7_18_2024/25_phase_data/dicom_recon/dicom_recon'

scan_dirs = glob.glob(all_scans+"/*_phase_*")

for scan_dir in scan_dirs:
    print(scan_dir)

    scans = [scan_dir] # glob.glob(scan_dir+"/*")

    out_dir = '/deneb_disk/disc_mri/for_Ye_7_18_2024/25_phase_data/nifti_phase' + scan_dir.split('phase')[-1]
    #scan_dir.replace('dicom_recon', 'nifti_phase'+scan_dir.split('phase')[-1])

    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)

    for s in scans:
        print(s)

        dicom2nifti.convert_dir.convert_directory(s, out_dir, compression=True)












