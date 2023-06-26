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


te = 98
MAX_COMB = 20

subdir = "/deneb_disk/fetal_scan_6_2_2023/VOL632_nii_rot"
template = subdir + f"/p40_t2_haste_cor_head_te{te}_p.nii.gz"
mask = subdir + f"/p40_t2_haste_cor_head_te{te}_p.mask.nii.gz"
fetal_atlas = "/home/ajoshi/projects/disc_mri/fetal_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA33.nii.gz"
fetal_atlas_seg = "/home/ajoshi/projects/disc_mri/fetal_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA33_regional.nii.gz"
fetal_atlas_tissue = "/home/ajoshi/projects/disc_mri/fetal_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA33_tissue.nii.gz"

stacks = glob.glob(subdir + f"/*head*te{te}*p.nii.gz")

res = 1
th = 3


num_stacks = len(stacks)


a = np.load("ssim_mse.npz")
val_ssim=a['val_ssim']
val_mse=a['val_mse']

x = range(1, len(stacks) + 1)

plt.xticks(np.arange(min(x), max(x) + 1, 1.0))

plt.plot(x[2:], val_ssim[2:])
plt.savefig("ssim.png")

plt.close()

plt.xticks(np.arange(min(x), max(x) + 1, 1.0))

plt.plot(x[2:], val_mse[2:])
plt.savefig("mse.png")

