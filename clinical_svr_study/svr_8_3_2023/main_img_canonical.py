import nilearn.image as ni
import numpy as np
import os
import glob


import matplotlib.pyplot as plt

from nilearn.image import resample_img

import nibabel as nib


for i in range(31):

    sub = f'{i+1:04d}'

    nii_img = '/home/ajoshi/projects/disc_mri/clinical_svr_study/svr_8_3_2023/svr_aligned_randomized_31/RND_'+sub+'_SVR_aligned.nii.gz'
    nii_img_out = '/home/ajoshi/projects/disc_mri/clinical_svr_study/svr_8_3_2023/svr_aligned_randomized_31/RND_'+sub+'_SVR_aligned_canonical.nii.gz'

    img = nib.load(nii_img)
    img2 = nib.as_closest_canonical(img)

    img2.to_filename(nii_img_out)
