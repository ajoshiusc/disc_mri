# This file converts a batch of acquisitions at DISC to nifti files

import dicom2nifti
import glob
import os

#scans_dir = '/deneb_disk/fetal_scan_8_3_2022/data'
scans_dir = '/deneb_disk/fetal_scan_6_2_2023'
scans = glob.glob(scans_dir+"/*2")

#out_dir = '/deneb_disk/fetal_scan_8_3_2022/nifti'
out_dir = '/deneb_disk/fetal_scan_6_2_2023/VOL632_nii'

if not os.path.isdir(out_dir):
    os.mkdir(out_dir)

for s in scans:
    print(s)

    dicom2nifti.convert_dir.convert_directory(s, out_dir, compression=True)













