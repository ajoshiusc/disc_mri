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
from itertools import combinations

import matplotlib.pyplot as plt

subdir = "/deneb_disk/fetal_scan_6_2_2023/VOL632_nii_rot"
template = subdir + "/p40_t2_haste_cor_head_te98_p.nii.gz"
mask = subdir + "/p40_t2_haste_cor_head_te98_p.mask.nii.gz"
fetal_atlas = "/home/ajoshi/projects/disc_mri/fetal_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA33.nii.gz"
fetal_atlas_seg = "/home/ajoshi/projects/disc_mri/fetal_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA33_regional.nii.gz"
fetal_atlas_tissue = "/home/ajoshi/projects/disc_mri/fetal_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA33_tissue.nii.gz"

stacks_all = glob.glob(subdir + "/*head*te98*p.nii.gz")

res = 1
th = 3


for num_stacks in range(1, len(stacks_all) + 1):
    for ns, stacks in enumerate(combinations(stacks_all, num_stacks)):
        str_stacks = ""
        str_th = ""

        for s in stacks:
            str_stacks += " " + s
            str_th += " " + str(th)

        outsvr = f"outsvr/svr_te98_numstacks_{num_stacks}_iter_{ns}.nii.gz"

        cmd = (
            "mirtksvr reconstruct "
            + outsvr
            + " "
            + str(num_stacks)
            + str_stacks
            + " --resolution "
            + str(res)
        )

        cmd += " --thickness" + str_th + " --template " + template + " --mask " + mask

        print(cmd)
        os.system(cmd)
