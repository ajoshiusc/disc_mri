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

subdir = "/deneb_disk/fetal_data_8_11_2023/nifti_data_rot"
template = subdir + "/p21_t2_haste_tra_head_te98_p.nii.gz"
mask = subdir + '/p21_t2_haste_tra_head_te98_p.mask.nii.gz'
fetal_atlas = "/deneb_disk/disc_mri/fetal_atlas//CRL_FetalBrainAtlas_2017v3/STA30.nii.gz"
fetal_atlas_seg = "/deneb_disk/disc_mri/fetal_atlas//CRL_FetalBrainAtlas_2017v3/STA30_regional.nii.gz"
fetal_atlas_tissue = "/deneb_disk/disc_mri/fetal_atlas//CRL_FetalBrainAtlas_2017v3/STA30_tissue.nii.gz"

outsvr_dir = "/deneb_disk/disc_mri/scan_8_11_2023/outsvr"

stacks = glob.glob(subdir + f"/*head*te{te}*p.nii.gz")

res = 1
th = 3

num_stacks_max = len(stacks)

# Use highest number of stacks for registration
outsvr_max = f"{outsvr_dir}/svr_te{te}_numstacks_{num_stacks_max}_iter_{0}_masked.nii.gz"
outsvr_max_aligned = f"{outsvr_dir}/svr_te{te}_numstacks_{num_stacks_max}_aligned.nii.gz"

# Register the highest quality reconstruction to atlas
if not os.path.exists(outsvr_max_aligned):
    cmd = (
        "flirt -in "
        + outsvr_max
        + " -ref "
        + fetal_atlas
        + " -out "
        + outsvr_max_aligned
        + " -dof 6 -omat "
        + f"reorient_te{te}_max.mat"
        + " -searchrx -180 180 -searchry -180 180 -searchrz -180 180 -cost mutualinfo"
    )
    print(cmd)
    os.system(cmd)

# Since SVR reconstructions are registered to atlas space, use original tissue atlas directly
tissue_atlas = fetal_atlas_tissue

print("Registration done - using original tissue atlas since images are in atlas space")

# Apply the same transformation to align all other reconstructions
for num_stacks, ns in product(range(1, len(stacks) + 1), range(MAX_COMB)):
    outsvr = f"{outsvr_dir}/svr_te{te}_numstacks_{num_stacks}_iter_{ns}.nii.gz"
    outsvr_aligned = f"{outsvr_dir}/svr_te{te}_numstacks_{num_stacks}_iter_{ns}_aligned.nii.gz"

    if os.path.exists(outsvr_aligned) or not os.path.exists(outsvr):
        continue

    cmd = (
        "flirt -in "
        + outsvr
        + " -ref "
        + fetal_atlas
        + " -out "
        + outsvr_aligned
        + " -applyxfm -init "
        + f"reorient_te{te}_max.mat"
    )
    print(cmd)
    os.system(cmd)

def calculate_wm_gm_contrast_and_snr(image_data, tissue_data):
    """
    Calculate WM to GM contrast and SNR
    Assumes tissue labels: GM=1, WM=2 (adjust based on your atlas)
    """
    # Define tissue labels based on labelnames.csv and what's present in STA30
    GM_LABELS = [112, 113]  # Cortical_Plate_L, Cortical_Plate_R
    
    # For GA30, white matter is represented by developmental zones:
    WM_LABELS = [114, 115, 116, 117, 118, 119, 122, 123]  # All white matter developmental zones

    # Extract tissue regions
    gm_mask = np.isin(tissue_data, GM_LABELS)
    wm_mask = np.isin(tissue_data, WM_LABELS)

    if np.sum(gm_mask) == 0 or np.sum(wm_mask) == 0:
        return np.nan, np.nan, np.nan, np.nan

    # Calculate mean intensities
    gm_mean = np.mean(image_data[gm_mask])
    wm_mean = np.mean(image_data[wm_mask])

    # Calculate standard deviations
    gm_std = np.std(image_data[gm_mask])
    wm_std = np.std(image_data[wm_mask])

    # WM to GM contrast ratio
    contrast_ratio = wm_mean / gm_mean if gm_mean != 0 else np.nan

    # Contrast-to-noise ratio (CNR)
    cnr = abs(wm_mean - gm_mean) / np.sqrt((wm_std**2 + gm_std**2) / 2)

    # Signal-to-noise ratio for GM and WM
    snr_gm = gm_mean / gm_std if gm_std != 0 else np.nan
    snr_wm = wm_mean / wm_std if wm_std != 0 else np.nan

    return contrast_ratio, cnr, snr_gm, snr_wm

# Load warped tissue map
# Since images are now in atlas space, use the atlas tissue labels directly
tissue_img = load_img(fetal_atlas_tissue)
tissue_data = tissue_img.get_fdata()

# Initialize arrays for metrics
contrast_ratios = np.zeros((len(stacks), MAX_COMB))
cnr_values = np.zeros((len(stacks), MAX_COMB))
snr_gm_values = np.zeros((len(stacks), MAX_COMB))
snr_wm_values = np.zeros((len(stacks), MAX_COMB))

print("Calculating WM-GM contrast and SNR...")

for ns, i in product(range(len(stacks)), range(MAX_COMB)):
    outsvr_aligned = f"{outsvr_dir}/svr_te{te}_numstacks_{ns+1}_iter_{i}_aligned.nii.gz"
    
    if not os.path.exists(outsvr_aligned):
        contrast_ratios[ns, i] = np.nan
        cnr_values[ns, i] = np.nan
        snr_gm_values[ns, i] = np.nan
        snr_wm_values[ns, i] = np.nan
        continue
    
    # Load image data
    img_data = load_img(outsvr_aligned).get_fdata()
    
    # Calculate metrics
    contrast_ratio, cnr, snr_gm, snr_wm = calculate_wm_gm_contrast_and_snr(img_data, tissue_data)
    
    contrast_ratios[ns, i] = contrast_ratio
    cnr_values[ns, i] = cnr
    snr_gm_values[ns, i] = snr_gm
    snr_wm_values[ns, i] = snr_wm

print("Metrics calculated")

# Save results
np.savez("wm_gm_contrast_snr.npz", 
         contrast_ratios=contrast_ratios,
         cnr_values=cnr_values, 
         snr_gm_values=snr_gm_values,
         snr_wm_values=snr_wm_values)

# Plot results
x = range(1, len(stacks) + 1)

# Calculate mean and std across iterations
contrast_mean = np.nanmean(contrast_ratios, axis=1)
contrast_std = np.nanstd(contrast_ratios, axis=1)
cnr_mean = np.nanmean(cnr_values, axis=1)
cnr_std = np.nanstd(cnr_values, axis=1)
snr_gm_mean = np.nanmean(snr_gm_values, axis=1)
snr_gm_std = np.nanstd(snr_gm_values, axis=1)
snr_wm_mean = np.nanmean(snr_wm_values, axis=1)
snr_wm_std = np.nanstd(snr_wm_values, axis=1)

# Plot WM/GM Contrast Ratio
plt.figure(figsize=(12, 8))
plt.subplot(2, 2, 1)
plt.errorbar(x, contrast_mean, yerr=contrast_std, marker='o')
plt.xlabel('Number of Stacks')
plt.ylabel('WM/GM Contrast Ratio')
plt.title('WM to GM Contrast vs Number of Stacks')
plt.xticks(x)
plt.grid(True)

# Plot CNR
plt.subplot(2, 2, 2)
plt.errorbar(x, cnr_mean, yerr=cnr_std, marker='o', color='red')
plt.xlabel('Number of Stacks')
plt.ylabel('Contrast-to-Noise Ratio')
plt.title('CNR vs Number of Stacks')
plt.xticks(x)
plt.grid(True)

# Plot GM SNR
plt.subplot(2, 2, 3)
plt.errorbar(x, snr_gm_mean, yerr=snr_gm_std, marker='o', color='green')
plt.xlabel('Number of Stacks')
plt.ylabel('GM SNR')
plt.title('Gray Matter SNR vs Number of Stacks')
plt.xticks(x)
plt.grid(True)

# Plot WM SNR
plt.subplot(2, 2, 4)
plt.errorbar(x, snr_wm_mean, yerr=snr_wm_std, marker='o', color='orange')
plt.xlabel('Number of Stacks')
plt.ylabel('WM SNR')
plt.title('White Matter SNR vs Number of Stacks')
plt.xticks(x)
plt.grid(True)

plt.tight_layout()
plt.savefig("wm_gm_contrast_snr_analysis.png", dpi=300)
plt.close()

print("Analysis complete. Results saved to wm_gm_contrast_snr.npz and wm_gm_contrast_snr_analysis.png")
