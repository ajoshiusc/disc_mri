import nilearn.image as ni
from sklearn.feature_extraction import img_to_graph
import numpy as np
import os
import SimpleITK as sitk
import glob
from monai.metrics.regression import SSIMMetric, MSEMetric
from nilearn.image import load_img
from monai.transforms import EnsureChannelFirst
from tqdm import tqdm
from monai.losses.ssim_loss import SSIMLoss
from torch.nn import MSELoss

# from itertools import product
from tqdm.contrib.itertools import product

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sb
from nilearn.plotting import plot_anat
from itertools import product

import nibabel as nib

te = 272
MAX_COMB = 1

subdir = "/deneb_disk/fetal_scan_6_2_2023/VOL632_nii_rot"
template = subdir + "/p28_t2_haste_sag_head_te272_p.nii.gz"
mask = subdir + "/p28_t2_haste_sag_head_te272_p.mask.nii.gz"
fetal_atlas = "/home/ajoshi/projects/disc_mri/fetal_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA33.nii.gz"
fetal_atlas_seg = "/home/ajoshi/projects/disc_mri/fetal_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA33_regional.nii.gz"
fetal_atlas_tissue = "/home/ajoshi/projects/disc_mri/fetal_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA33_tissue.nii.gz"

stacks = glob.glob(subdir + f"/*head*te{te}*p.nii.gz")[:12]

res = 1
th = 3

STACKS=[0,2,5,8,11]
num_stacks = len(STACKS)

TEs = [98, 140, 181, 272]

SZ = load_img(fetal_atlas).shape


array_data = np.zeros((num_stacks * SZ[0], len(TEs) * SZ[1], SZ[2]))

for it, te in enumerate(TEs):
    for n, st in enumerate(STACKS):
        fname = f"/home/ajoshi/projects/disc_mri/fetal_mri/outsvr/svr_te{te}_numstacks_{st+1}_iter_0_aligned.nii.gz"
        img = load_img(fname).get_fdata()

        array_data[
            (n) * SZ[0] : (n + 1) * SZ[0], (it) * SZ[1] : (it + 1) * SZ[1], :
        ] = img

        print(it, n)


affine = np.diag([.8, .8, .8, 1])
array_img = nib.Nifti1Image(array_data, affine)
array_img.to_filename("concat_z.nii.gz")

