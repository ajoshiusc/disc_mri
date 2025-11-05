# This file converts a batch of acquisitions at DISC to nifti files

import dicom2nifti
import glob
import os
import dicom2nifti.settings as settings
settings.disable_validate_slice_increment()


#scans_dir = '/deneb_disk/fetal_scan_8_3_2022/data'
scans_dir = '/deneb_disk/disc_mri/scan_10_23_2025/Vol1375_20251023/Vol1375_20251023/'
scans = glob.glob(scans_dir+"/*")

#out_dir = '/deneb_disk/fetal_scan_8_3_2022/nifti'
out_dir = '/deneb_disk/disc_mri/scan_10_23_2025/nifti'

if not os.path.isdir(out_dir):
    os.mkdir(out_dir)

for s in scans:
    print(s)

    dicom2nifti.convert_dir.convert_directory(s, out_dir, compression=True)













