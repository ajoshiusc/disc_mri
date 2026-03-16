#!/usr/bin/env python3
"""
Shared configuration, constants, and utility functions for the
multi-step fetal MRI TE analysis pipeline.
"""

import os
import glob
import re
import numpy as np
import nibabel as nib
import matplotlib.pyplot as plt
import torch
from monai.losses.ssim_loss import SSIMLoss
from torch.nn import MSELoss

# ---------------------------------------------------------------------------
# Plot style
# ---------------------------------------------------------------------------
plt.rcParams.update({
    'font.size': 12, 'axes.titlesize': 14, 'axes.labelsize': 12,
    'xtick.labelsize': 11, 'ytick.labelsize': 11, 'legend.fontsize': 10,
    'figure.titlesize': 16, 'font.family': 'DejaVu Sans',
    'axes.linewidth': 1.5, 'grid.linewidth': 0.8,
    'lines.linewidth': 2.0, 'lines.markersize': 8,
})

# ---------------------------------------------------------------------------
# Subject registry
# ---------------------------------------------------------------------------
SUBJECTS = {
    "subj_8_11_2023":        ("/deneb_disk/disc_mri/scan_8_11_2023/outsvr",                          "svr_te{te}*numstacks_*"),
    "subj_9_12_2023":        ("/deneb_disk/disc_mri/scan_9_12_2023/outsvr",                           "svr_te{te}*numstacks_*"),
    "subj_11_3_2023_babya":  ("/deneb_disk/disc_mri/scan_11_3_2023_twins_nii_rot/outsvr",             "svr_te{te}_babya*numstacks_*"),
    "subj_11_3_2023_babyb":  ("/deneb_disk/disc_mri/scan_11_3_2023_twins_nii_rot/outsvr",             "svr_te{te}_babyb*numstacks_*"),
    "subj_3_20_2024":        ("/deneb_disk/disc_mri/scan_3_20_2024/outsvr",                           "svr_te{te}*numstacks_*"),
    "subj_10_23_2025":       ("/home/ajoshi/project2_ajoshi_27/data/disc_mri/scan_10_23_2025/outsvr", "svr_te{te}*numstacks_*"),
    "subj_12_03_2025":       ("/home/ajoshi/project2_ajoshi_27/data/disc_mri/scan_12_03_2025/outsvr", "svr_te{te}*numstacks_*"),
    "subj_1_8_2026":         ("/home/ajoshi/project2_ajoshi_27/data/disc_mri/scan_1_8_2026/outsvr",   "svr_te{te}*numstacks_*"),
    "subj_2_6_2026":         ("/home/ajoshi/project2_ajoshi_27/data/disc_mri/scan_2_6_2026/outsvr",   "svr_te{te}*numstacks_*"),
    "subj_2_9_2026":         ("/home/ajoshi/project2_ajoshi_27/data/disc_mri/scan_2_9_2026/outsvr",   "svr_te{te}*numstacks_*"),
}

SUBJECT_GA = {
    "subj_8_11_2023":       30,
    "subj_9_12_2023":       37,
    "subj_11_3_2023_babya": 30,
    "subj_11_3_2023_babyb": 30,
    "subj_3_20_2024":       24,
    "subj_10_23_2025":      38,
    "subj_12_03_2025":      29,
    "subj_1_8_2026":        36,
    "subj_2_6_2026":        37,
    "subj_2_9_2026":        35,
}

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
FETAL_ATLAS_DIR = "/deneb_disk/disc_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3"
CACHE_DIR       = "/home/ajoshi/Projects/disc_mri/fetal_mri/atlas_registrations"
OUTPUT_DIR      = "/home/ajoshi/Projects/disc_mri/fetal_mri"

# Intermediate file produced by step 2 and consumed by step 3
FINAL_DATA_JSON = os.path.join(OUTPUT_DIR, "final_data.json")

os.makedirs(CACHE_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Analysis parameters
# ---------------------------------------------------------------------------
OUTLIER_REJECTION_RATE = 0.4
TE_VALUES              = [98, 140, 181, 272]

# Minimum length of a gap-free (step-1) consecutive stack sequence required
# to include a subject/TE combination.
MIN_CONSECUTIVE_STACKS = 4

# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def atlas_ga_str(ga: int) -> str:
    """Return the atlas filename GA suffix (e.g. '36exp' for GA >= 36)."""
    return f"{ga}exp" if ga >= 36 else str(ga)


def has_consecutive_stacks(stack_keys) -> bool:
    """True only when sorted stack counts are gap-free with step 1 and
    have at least MIN_CONSECUTIVE_STACKS entries."""
    s = sorted(stack_keys)
    if len(s) < MIN_CONSECUTIVE_STACKS:
        return False
    for i in range(1, len(s)):
        if s[i] - s[i - 1] != 1:
            return False
    return True


def get_subject_files(directory: str, pat_template: str, te: int) -> dict:
    """Return {num_stacks: [file_path, ...]} for the given subject/TE."""
    pat = pat_template.format(te=te)
    all_files = glob.glob(os.path.join(directory, pat + ".nii.gz"))
    native_files = [f for f in all_files if not f.endswith("_aligned.nii.gz")]

    stack_dict: dict = {}
    for f in native_files:
        bname = os.path.basename(f)
        m = re.search(r'numstacks_(\d+)', bname)
        if m:
            stacks = int(m.group(1))
            stack_dict.setdefault(stacks, []).append(f)
    return stack_dict


def get_tissue_mask_for_subject(subj_name: str) -> np.ndarray:
    ga     = SUBJECT_GA.get(subj_name, 30)
    ga_str = atlas_ga_str(ga)
    tissue_path = os.path.join(FETAL_ATLAS_DIR, f"STA{ga_str}_tissue.nii.gz")
    if not os.path.exists(tissue_path):
        raise FileNotFoundError(f"Missing tissue atlas for GA {ga}: {tissue_path}")
    return nib.load(tissue_path).get_fdata()


def calculate_ssim_nmse(img_data: np.ndarray, ref_data: np.ndarray):
    if img_data.shape != ref_data.shape:
        return np.nan, np.nan

    img_vol = np.expand_dims(img_data, axis=(0, 1))
    ref_vol = np.expand_dims(ref_data, axis=(0, 1))
    t_img = torch.tensor(img_vol, dtype=torch.float32)
    t_ref = torch.tensor(ref_vol, dtype=torch.float32)

    img_valid = t_img[t_img > 0]
    ref_valid = t_ref[t_ref > 0]
    if len(img_valid) == 0 or len(ref_valid) == 0:
        return np.nan, np.nan

    img_max, img_min = img_valid.max(), img_valid.min()
    ref_max, ref_min = ref_valid.max(), ref_valid.min()

    t_img_norm = torch.zeros_like(t_img)
    t_img_norm[t_img > 0] = (t_img[t_img > 0] - img_min) / (img_max - img_min + 1e-8)

    t_ref_norm = torch.zeros_like(t_ref)
    t_ref_norm[t_ref > 0] = (t_ref[t_ref > 0] - ref_min) / (ref_max - ref_min + 1e-8)

    ssim = 1 - SSIMLoss(spatial_dims=3)(t_img_norm, t_ref_norm).item()
    nmse = (MSELoss()(t_img_norm, t_ref_norm) / ((t_ref_norm ** 2).mean() + 1e-8)).item()
    return ssim, nmse


def calculate_tissue_metrics(img_data: np.ndarray, tissue_data: np.ndarray):
    GM_LABELS = [112, 113]
    WM_LABELS = [114, 115, 116, 117, 118, 119, 122, 123]
    gm_mask = np.isin(tissue_data, GM_LABELS)
    wm_mask = np.isin(tissue_data, WM_LABELS)

    if np.sum(gm_mask) == 0 or np.sum(wm_mask) == 0:
        return np.nan, np.nan, np.nan, np.nan

    gm_signal = img_data[gm_mask]
    wm_signal = img_data[wm_mask]

    mu_gm, sig_gm = np.mean(gm_signal), np.std(gm_signal)
    mu_wm, sig_wm = np.mean(wm_signal), np.std(wm_signal)

    cr    = mu_gm / mu_wm if mu_wm > 0 else np.nan
    cnr   = (abs(mu_wm - mu_gm) / np.sqrt((sig_wm ** 2 + sig_gm ** 2) / 2)
             if (sig_wm > 0 or sig_gm > 0) else np.nan)
    snr_gm = mu_gm / sig_gm if sig_gm > 0 else np.nan
    snr_wm = mu_wm / sig_wm if sig_wm > 0 else np.nan

    return cr, cnr, snr_gm, snr_wm
