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

te = 140
MAX_COMB = 1

subdir = "/deneb_disk/fetal_scan_6_2_2023/VOL632_nii_rot"
template = subdir + '/p19_t2_haste_cor_head_te140_p.nii.gz'
mask = subdir + '/p19_t2_haste_cor_head_te140_p.mask.nii.gz'
fetal_atlas = "/home/ajoshi/projects/disc_mri/fetal_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA33.nii.gz"
fetal_atlas_seg = "/home/ajoshi/projects/disc_mri/fetal_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA33_regional.nii.gz"
fetal_atlas_tissue = "/home/ajoshi/projects/disc_mri/fetal_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA33_tissue.nii.gz"

stacks = glob.glob(subdir + f"/*head*te{te}*p.nii.gz")

res = 1
th = 3


num_stacks = len(stacks)


a = np.load("ssim_mse.npz")
val_ssim = a["val_ssim"]
val_mse = a["val_mse"]

x = np.arange(1, len(stacks) + 1)
y = np.arange(MAX_COMB)


data = pd.DataFrame(val_mse.T, columns=x)
m = pd.melt(data, var_name="column", value_name="value")
m = m.rename(columns={"column": "num_stacks", "value": "mse"})
sb.lineplot(data=m, x="num_stacks", y="mse")
plt.savefig(f"te{te}_mse_vs_num_stacks.png")
plt.close()

data = pd.DataFrame(val_ssim.T, columns=x)
m = pd.melt(data, var_name="column", value_name="value")
m = m.rename(columns={"column": "num_stacks", "value": "ssim"})
sb.lineplot(data=m, x="num_stacks", y="ssim")
plt.savefig(f"te{te}_ssim_vs_num_stacks.png")
plt.close()

print("done")


for i in range(num_stacks):
    fname = f"/home/ajoshi/projects/disc_mri/fetal_mri/outsvr/svr_te{te}_numstacks_{i+1}_iter_0_aligned.nii.gz"
    plot_anat(
        anat_img=fname,
        cut_coords=[0],
        draw_cross=False,
        vmin=0,
        vmax=1100,
        display_mode="y",
        annotate=False,
    )
    plt.draw()
    plt.savefig(f"svr_te{te}_numstacks_{i+1}_iter_0_aligned.png")
