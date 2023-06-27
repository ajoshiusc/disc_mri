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

x = np.arange(1, len(stacks) + 1)
y = np.arange(MAX_COMB)


data =pd.DataFrame(val_mse.T,columns=x)

m=pd.melt(data,var_name='column',value_name='value')

sb.lineplot(data=m,x='column',y='value')

plt.draw()
plt.show()

print('done')

