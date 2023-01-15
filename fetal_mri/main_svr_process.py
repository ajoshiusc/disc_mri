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

str_stacks = ''
str_th = ''

for s in stacks:
    str_stacks += ' ' + s
    str_th += ' ' + str(th)



cmd = 'mirtksvr reconstruct ' + outsvr + ' ' + str(len(stacks)) + str_stacks + ' --resolution ' + str(res) 

cmd += ' --thickness' + str_th + ' --template ' + template + ' --mask ' + mask


print(cmd)
os.system(cmd)


