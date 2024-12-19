# This file converts a batch of acquisitions at DISC to nifti files

import dicom2nifti
import glob
import os
from itertools import product
import dicom2nifti.settings as settings

settings.disable_validate_slice_increment()


# scans_dir = '/deneb_disk/fetal_scan_8_3_2022/data'
scans_dir_top = ("/deneb_disk/disc_mri/for_Ye_12_11_2024_4subjects/dicoms/unzipped")

expmt_dir_all = glob.glob(scans_dir_top + "/*")

#phase_fixed = 11

for phase, expmt_dir in product(range(25), expmt_dir_all):

    # stack_id =stack_dir.split('ssfp_')[-1][0:8]
    stack_dir_all = glob.glob(expmt_dir +"/dicom_recon_arrhythmia_reject/*")
    if len(stack_dir_all) == 0:
        stack_dir_all = glob.glob(expmt_dir + "/vol*/*")
    
    

    for stack_dir in stack_dir_all:

        inp_dir = expmt_dir + f'/phase_{phase+1:02d}'
        out_expmt_dir = "/deneb_disk/disc_mri/for_Ye_12_11_2024_4subjects/nifti_files/" + expmt_dir.split('/')[-1] 

        if not os.path.isdir(out_expmt_dir):
            os.mkdir(out_expmt_dir)
        
        out_stack_dir = out_expmt_dir #+ '/' + stack_dir.split('/')[-1]

        if not os.path.isdir(out_stack_dir):
            os.mkdir(out_stack_dir)

        out_dir = out_stack_dir + f'/phase_{phase+1:02d}'

        if not os.path.isdir(out_dir):
            os.mkdir(out_dir)

        phase_dir = stack_dir + f'/phase_{phase+1:02d}'        

        dicom2nifti.convert_dir.convert_directory(phase_dir, out_dir, compression=True)
        print("Converted", phase_dir, "to", out_dir)


