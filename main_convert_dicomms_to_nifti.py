# This file converts a batch of acquisitions at DISC to nifti files

import dicom2nifti
import glob
import os

scans_dir = '/deneb_disk/fetal_scan_8_3_2022/data'

scans = glob.glob(scans_dir+"/*")
out_dir = '/deneb_disk/fetal_scan_8_3_2022/nifti'

if not os.path.isdir(out_dir):
    os.mkdir(out_dir)

for s in scans:
    print(s)

    dicom2nifti.convert_dir.convert_directory(s, out_dir, compression=True)













