# This file converts a batch of acquisitions at DISC to nifti files

import dicom2nifti
import glob
import os

#scans_dir = '/deneb_disk/fetal_scan_8_3_2022/data'
scans_dir = '/deneb_disk/low_field_pns_device_fmri/11_16_2022/VOL504_PNS_22_11_16-15_46_28-STD-1_3_12_2_1107_5_2_18_41185/SOPHIA_LIBRARY_20221116_160143_945000'
scans = glob.glob(scans_dir+"/E*")

#out_dir = '/deneb_disk/fetal_scan_8_3_2022/nifti'
out_dir = '/deneb_disk/low_field_pns_device_fmri/11_16_2022/nii_files'

if not os.path.isdir(out_dir):
    os.mkdir(out_dir)

for s in scans:
    print(s)

    dicom2nifti.convert_dir.convert_directory(s, out_dir, compression=True)













