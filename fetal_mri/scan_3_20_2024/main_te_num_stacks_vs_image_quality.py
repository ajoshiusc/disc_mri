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


te = 140
MAX_COMB = 20


subdir = "/deneb_disk/disc_mri/scan_3_20_2024/nifti_rot"
template = subdir + "/p20_t2_haste_cor_head_te140_p.nii.gz"
mask = subdir + "/p20_t2_haste_cor_head_te140_p.mask.nii.gz"
fetal_atlas = (
    "/deneb_disk/disc_mri/fetal_atlas//CRL_FetalBrainAtlas_2017v3/STA30.nii.gz"
)
fetal_atlas_seg = (
    "/deneb_disk/disc_mri/fetal_atlas//CRL_FetalBrainAtlas_2017v3/STA30_regional.nii.gz"
)
fetal_atlas_tissue = (
    "/deneb_disk/disc_mri/fetal_atlas//CRL_FetalBrainAtlas_2017v3/STA30_tissue.nii.gz"
)

outsvr_dir = "/deneb_disk/disc_mri/scan_3_20_2024/outsvr"

"""
subdir = "/deneb_disk/fetal_data_8_11_2023/nifti_data_rot"
template = subdir + "/p10_t2_haste_tra_head_te140_p.nii.gz"
mask = subdir + '/p10_t2_haste_tra_head_te140_p.mask.nii.gz'
fetal_atlas = "/deneb_disk/disc_mri/fetal_atlas//CRL_FetalBrainAtlas_2017v3/STA30.nii.gz"
fetal_atlas_seg = "/deneb_disk/disc_mri/fetal_atlas//CRL_FetalBrainAtlas_2017v3/STA30_regional.nii.gz"
fetal_atlas_tissue = "/deneb_disk/disc_mri/fetal_atlas//CRL_FetalBrainAtlas_2017v3/STA30_tissue.nii.gz"

subdir = "/deneb_disk/fetal_data_8_11_2023/nifti_data_rot"
template = subdir + "/p34_t2_haste_tra_head_te181_p.nii.gz"
mask = subdir + '/p34_t2_haste_tra_head_te181_p.mask.nii.gz'

fetal_atlas = "/deneb_disk/disc_mri/fetal_atlas//CRL_FetalBrainAtlas_2017v3/STA30.nii.gz"
fetal_atlas_seg = "/deneb_disk/disc_mri/fetal_atlas//CRL_FetalBrainAtlas_2017v3/STA30_regional.nii.gz"
fetal_atlas_tissue = "/deneb_disk/disc_mri/fetal_atlas//CRL_FetalBrainAtlas_2017v3/STA30_tissue.nii.gz"
"""

stacks = glob.glob(subdir + f"/*head*te{te}*p.nii.gz")

res = 1
th = 3


num_stacks = len(stacks)

outsvr = f"{outsvr_dir}/svr_te{te}_numstacks_{num_stacks}_iter_{0}.nii.gz"
outsvr_aligned = f"{outsvr_dir}/svr_te{te}_aligned.nii.gz"

if not os.path.exists(outsvr_aligned):

    cmd = (
        "flirt -in "
        + outsvr
        + " -ref "
        + fetal_atlas
        + " -out "
        + outsvr_aligned
        + " -dof 6 -omat "
        + f"reorient_te{te}.mat"
        + " -searchrx -180 180 -searchry -180 180 -searchrz -180 180 -cost mutualinfo"
    )

    print(cmd)
    os.system(cmd)

print("registration of svr to atlas done")

num_stacks_range = (3, 6, 9, 10)  # range(1, len(stacks) + 1)

for num_stacks, ns in product(num_stacks_range, range(MAX_COMB)):
    outsvr = f"{outsvr_dir}/svr_te{te}_numstacks_{num_stacks}_iter_{ns}.nii.gz"
    outsvr_aligned = (
        f"{outsvr_dir}/svr_te{te}_numstacks_{num_stacks}_iter_{ns}_aligned.nii.gz"
    )

    if os.path.exists(outsvr_aligned):
        continue

    cmd = (
        "flirt -in "
        + outsvr
        + " -ref "
        + fetal_atlas
        + " -out "
        + outsvr_aligned
        + " -applyxfm -init "
        + f"reorient_te{te}.mat"
    )

    print(cmd)
    os.system(cmd)

print("registration of svr to atlas done")