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
MAX_COMB = 20

subdir = "/deneb_disk/fetal_scan_9_12_2023/vol0700_nii_rot"
template = subdir + "/p11_t2_haste_sag_head_te140_p.nii.gz"
mask = subdir + "/p11_t2_haste_sag_head_te140_p.mask.nii.gz"


fetal_atlas = "/deneb_disk/disc_mri/fetal_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA37exp.nii.gz"
fetal_atlas_seg = "/deneb_disk/disc_mri/fetal_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA37exp_regional.nii.gz"
fetal_atlas_tissue = "/deneb_disk/disc_mri/fetal_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA37exp_tissue.nii.gz"


stacks = glob.glob(subdir + f"/*head*te{te}*p.nii.gz")[:12]

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
g = sb.lineplot(data=m, x="num_stacks", y="mse")
g.set(ylim=(0, None))

plt.savefig(f"te{te}_mse_vs_num_stacks.png")
plt.close()

data = pd.DataFrame(val_ssim.T, columns=x)
m = pd.melt(data, var_name="column", value_name="value")
m = m.rename(columns={"column": "num_stacks", "value": "ssim"})
g = sb.lineplot(data=m, x="num_stacks", y="ssim")
g.set(ylim=(0, None))
plt.savefig(f"te{te}_ssim_vs_num_stacks.png")
plt.close()

print("done")


for i in range(num_stacks):
    fname = f"/deneb_disk/disc_mri/scan_9_12_2023/outsvr/svr_te{te}_numstacks_{i+1}_iter_0_aligned.nii.gz"
    plot_anat(
        anat_img=fname,
        cut_coords=[0],
        draw_cross=False,
        vmin=0,
        vmax=1200,
        display_mode="y",
        annotate=False,
    )
    plt.draw()
    plt.savefig(f"svr_te{te}_numstacks_{i+1}_iter_0_aligned.png")
