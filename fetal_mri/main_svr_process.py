import nilearn.image as ni
from sklearn.feature_extraction import img_to_graph
import numpy as np
import os
import SimpleITK as sitk
import glob


subdir = '/deneb_disk/fetal_scan_1_9_2023/morning/nii_files_rot'
template = subdir + '/p28_t2_haste_sag_head_p.nii.gz'
mask = subdir + '/p28_t2_haste_sag_head_p_mask.nii.gz'

outsvr = subdir + '/outsvr.nii.gz'

stacks = glob.glob(subdir+'/*head*p.nii.gz')

res = 1
th = 3



for num_stacks in range(len(stacks)+1):

    str_stacks = ''
    str_th = ''

    for s in stacks[:num_stacks]:
        str_stacks += ' ' + s
        str_th += ' ' + str(th)


    outsvr = subdir + '/outsvr'+'_'+str(num_stacks)+'.nii.gz'
    outsvr_aligned = subdir + '/outsvr'+'_'+str(num_stacks)+'_aligned.nii.gz'

    cmd = 'mirtksvr reconstruct ' + outsvr + ' ' + \
        str(num_stacks) + str_stacks + ' --resolution ' + str(res)

    cmd += ' --thickness' + str_th + ' --template ' + template + ' --mask ' + mask

    print(cmd)
    os.system(cmd)

    cmd = 'flirt -in ' + outsvr + ' -ref /home/ajoshi/projects/disc_mri/fetal_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA31.nii.gz -out '+outsvr_aligned+' -dof 7 -omat reorient.mat -searchrx -180 180 -searchry -180 180 -searchrz -180 180'


    print(cmd)
    os.system(cmd)


