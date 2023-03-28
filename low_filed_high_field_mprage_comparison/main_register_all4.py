import os
import glob
import nibabel as nib
import numpy as np
import SimpleITK as sitk
from itertools import product

nsub = 5

outdir = '/deneb_disk/3T_vs_low_field/registered_data'
for n in range(1,nsub+1):

    sub1 = '/deneb_disk/3T_vs_low_field/3T_mprage_data_BrainSuite/subj' + str(n) + '_vol' + str(1) + '/T1.nii.gz'
    os.system('cp ' + sub1 + ' ' + outdir + f'/sub{n}_H1.nii.gz')
    sub2 = '/deneb_disk/3T_vs_low_field/3T_mprage_data_BrainSuite/subj' + str(n) + '_vol' + str(2) + '/T1.nii.gz'
    sub2w = outdir + f'/sub{n}_H2_to_H1.nii.gz'
    cmd = f'flirt -ref {sub1} -in {sub2} -out {sub2w}'
    os.system(cmd)

    sub2 = '/deneb_disk/3T_vs_low_field/low_field_mprage_data_BrainSuite/subj' + str(n) + '_vol' + str(1) + '/T1.nii.gz' 
    sub2w = outdir + f'/sub{n}_L1_to_H1.nii.gz'
    cmd = f'flirt -ref {sub1} -in {sub2} -out {sub2w}'
    os.system(cmd)

    sub2 = '/deneb_disk/3T_vs_low_field/low_field_mprage_data_BrainSuite/subj' + str(n) + '_vol' + str(2) + '/T1.nii.gz' 
    sub2w = outdir + f'/sub{n}__to_H1.nii.gz'
    cmd = f'flirt -ref {sub1} -in {sub2} -out {sub2w}'
    os.system(cmd)





