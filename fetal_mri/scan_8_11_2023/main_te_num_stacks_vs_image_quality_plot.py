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


all_te = [98, 140, 181, 272]
MAX_COMB = 20
num_stacks = 12
val_ssim = np.zeros((len(all_te), num_stacks, MAX_COMB))
val_mse = np.zeros((len(all_te), num_stacks, MAX_COMB))
wm_snr = np.zeros((len(all_te), num_stacks, MAX_COMB))

for i, te in enumerate(all_te):
    MAX_COMB = 20

    subdir = "/deneb_disk/fetal_data_8_11_2023/nifti_data_rot"
    template = subdir + "/p21_t2_haste_tra_head_te98_p.nii.gz"
    mask = subdir + "/p21_t2_haste_tra_head_te98_p.mask.nii.gz"
    fetal_atlas = "/home/ajoshi/projects/disc_mri/fetal_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA30.nii.gz"
    fetal_atlas_seg = "/home/ajoshi/projects/disc_mri/fetal_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA30_regional.nii.gz"
    fetal_atlas_tissue = "/home/ajoshi/projects/disc_mri/fetal_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA30_tissue.nii.gz"

    """
    subdir = "/deneb_disk/fetal_data_8_11_2023/nifti_data_rot"
    template = subdir + "/p10_t2_haste_tra_head_te140_p.nii.gz"
    mask = subdir + '/p10_t2_haste_tra_head_te140_p.mask.nii.gz'
    fetal_atlas = "/home/ajoshi/projects/disc_mri/fetal_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA30.nii.gz"
    fetal_atlas_seg = "/home/ajoshi/projects/disc_mri/fetal_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA30_regional.nii.gz"
    fetal_atlas_tissue = "/home/ajoshi/projects/disc_mri/fetal_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA30_tissue.nii.gz"

    subdir = "/deneb_disk/fetal_data_8_11_2023/nifti_data_rot"
    template = subdir + "/p34_t2_haste_tra_head_te181_p.nii.gz"
    mask = subdir + '/p34_t2_haste_tra_head_te181_p.mask.nii.gz'

    fetal_atlas = "/home/ajoshi/projects/disc_mri/fetal_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA30.nii.gz"
    fetal_atlas_seg = "/home/ajoshi/projects/disc_mri/fetal_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA30_regional.nii.gz"
    fetal_atlas_tissue = "/home/ajoshi/projects/disc_mri/fetal_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA30_tissue.nii.gz"

    subdir = "/deneb_disk/fetal_data_8_11_2023/nifti_data_rot"
    template = subdir + "/p47_t2_haste_cor_head_te272_p.nii.gz"
    mask = subdir + '/p47_t2_haste_cor_head_te272_p.mask.nii.gz'
    fetal_atlas = "/home/ajoshi/projects/disc_mri/fetal_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA30.nii.gz"
    fetal_atlas_seg = "/home/ajoshi/projects/disc_mri/fetal_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA30_regional.nii.gz"
    fetal_atlas_tissue = "/home/ajoshi/projects/disc_mri/fetal_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA30_tissue.nii.gz"

    """

    stacks = glob.glob(subdir + f"/*head*te{te}*p.nii.gz")[:12]

    res = 1
    th = 3

    num_stacks = len(stacks)

    a = np.load(f"ssim_mse_wm_snr_3_17_2025_{te}_nomask.npz")
    val_ssim[i,] = a["val_ssim"]
    val_mse[i,] = a["val_mse"]
    wm_snr[i,] = a["wm_snr"]

    x = np.arange(1, len(stacks) + 1)
    #y = np.arange(MAX_COMB)

    data = pd.DataFrame(val_mse[i].T, columns=x)
    m = pd.melt(data, var_name="column", value_name="value")
    m = m.rename(columns={"column": "num_stacks", "value": "mse"})
    g = sb.lineplot(data=m, x="num_stacks", y="mse")
    #g.set(ylim=(0, None))
    plt.savefig(f"te{te}_mse_vs_num_stacks.png")
    plt.close()

    data = pd.DataFrame(val_ssim[i].T, columns=x)
    m = pd.melt(data, var_name="column", value_name="value")
    m = m.rename(columns={"column": "num_stacks", "value": "ssim"})
    g = sb.lineplot(data=m, x="num_stacks", y="ssim")
    #g.set(ylim=(0, None))
    plt.savefig(f"te{te}_ssim_vs_num_stacks.png")
    plt.close()

    data = pd.DataFrame(wm_snr[i].T, columns=x)
    m = pd.melt(data, var_name="column", value_name="value")
    m = m.rename(columns={"column": "num_stacks", "value": "wm_snr"})
    g = sb.lineplot(data=m, x="num_stacks", y="wm_snr")
    #g.set(ylim=(0, None))
    plt.savefig(f"te{te}_wm_snr_vs_num_stacks.png")
    plt.close()

    for i in range(num_stacks):
        fname = f"/deneb_disk/disc_mri/scan_8_11_2023/outsvr/svr_te{te}_numstacks_{i+1}_iter_0_aligned.nii.gz"
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
        plt.close()

print("done")


for nstacks in [6]:

    data = pd.DataFrame(val_mse[:, nstacks - 1, :].T, columns=all_te)
    m = pd.melt(data, var_name="column", value_name="value")
    m = m.rename(columns={"column": "te", "value": "mse"})
    g = sb.lineplot(data=m, x="te", y="mse", marker='o')
    g.set(xticks=all_te)
    g.set(ylim=(0, None))
    plt.savefig(f"mse_vs_te_numstacks_{nstacks}.png")
    plt.close()

    data = pd.DataFrame(val_ssim[:, nstacks - 1, :].T, columns=all_te)
    m = pd.melt(data, var_name="column", value_name="value")
    m = m.rename(columns={"column": "te", "value": "ssim"})
    g = sb.lineplot(data=m, x="te", y="ssim", marker='o')
    g.set(xticks=all_te)
    g.set(ylim=(0, None))
    plt.savefig(f"ssim_vs_te_numstacks_{nstacks}.png")
    plt.close()

    data = pd.DataFrame(wm_snr[:, nstacks - 1, :].T, columns=all_te)
    m = pd.melt(data, var_name="column", value_name="value")
    m = m.rename(columns={"column": "te", "value": "wm_snr"})
    g = sb.lineplot(data=m, x="te", y="wm_snr", marker='o')
    g.set(xticks=all_te)
    g.set(ylim=(0, None))
    plt.savefig(f"wm_snr_vs_te_numstacks_{nstacks}.png")
    plt.close()
