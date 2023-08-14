import nilearn.image as ni
import numpy as np
import os
import glob


import matplotlib.pyplot as plt

from nilearn.image import resample_img

subdirs = glob.glob('/deneb_disk/SVR_8_3_2023/svr_output_manual_mask/Svr*/S*018_SVR.nii.gz')
atlas = '/home/ajoshi/projects/disc_mri/fetal_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA25.nii.gz'

atlas_1mm = resample_img(atlas,target_affine=np.eye(3))
atlas_1mm.set_data_dtype(np.int16)
atlas_1mm.to_filename('atlas_1mm.nii.gz')
atlas_1mm = 'atlas_1mm.nii.gz'

for sub in subdirs:

    subname = os.path.basename(sub)
    sub_aligned = subname[:-7]+'_aligned.nii.gz'
    cmd = 'flirt -in ' + sub + ' -ref '+ atlas +' -out ' + sub_aligned+' -dof 6 -omat reorient.mat -searchrx -180 180 -searchry -180 180 -searchrz -180 180 -cost corratio'

    print(cmd)
    os.system(cmd)
