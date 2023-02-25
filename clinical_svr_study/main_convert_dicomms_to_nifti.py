# This file converts a batch of acquisitions at DISC to nifti files

import dicom2nifti
import glob
import os
from zipfile import ZipFile
#scans_dir = '/deneb_disk/fetal_scan_8_3_2022/data'
scans_dir = '/deneb_disk/chla_data_2_21_2023'
sub_data = glob.glob(scans_dir+"/*.zip")

#out_dir = '/deneb_disk/fetal_scan_8_3_2022/nifti'
out_dir = '/deneb_disk/chla_data_2_21_2023/unzipped_dicomms'

if not os.path.isdir(out_dir):
    os.mkdir(out_dir)


for s in sub_data:

    dir, fname = os.path.split(s)
    out_sub_dir = out_dir + '/' + fname[:-4]

    if not os.path.isdir(out_sub_dir):
        os.mkdir(out_sub_dir)

    with ZipFile(s,"r") as zip_ref:
        zip_ref.extractall(out_sub_dir)
    

    d = glob.glob(out_sub_dir+'/*')
    scans = glob.glob(d[0]+'/*')

    if not os.path.isdir(scans_dir + '/sub_nii'):
        os.mkdir(scans_dir + '/sub_nii')
    
    for s in scans:
        print(s)

        out_sub_nii_dir = scans_dir + '/sub_nii/' + fname[:-4]

        if not os.path.isdir(out_sub_nii_dir):
            os.mkdir(out_sub_nii_dir)

        #dicom2nifti.convert_dir.convert_directory(s, out_sub_nii_dir)

        cmd = f'dcm2niix -z y -o \'{out_sub_nii_dir}\' \'{s}\''
        os.system(cmd)













