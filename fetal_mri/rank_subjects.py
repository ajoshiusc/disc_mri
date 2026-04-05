import os
import glob
import re
import numpy as np
import nibabel as nib
import torch
from monai.losses.ssim_loss import SSIMLoss  
from torch.nn import MSELoss

SUBJECTS = {
    "subj_8_11_2023": ("/deneb_disk/disc_mri/scan_8_11_2023/outsvr", "svr_te{te}*numstacks_*"),
    "subj_9_12_2023": ("/deneb_disk/disc_mri/scan_9_12_2023/outsvr", "svr_te{te}*numstacks_*"),
    "subj_11_3_2023_babya": ("/deneb_disk/disc_mri/scan_11_3_2023_twins_nii_rot/outsvr", "svr_te{te}_babya*numstacks_*"),
    "subj_11_3_2023_babyb": ("/deneb_disk/disc_mri/scan_11_3_2023_twins_nii_rot/outsvr", "svr_te{te}_babyb*numstacks_*"),
    "subj_3_20_2024": ("/deneb_disk/disc_mri/scan_3_20_2024/outsvr", "svr_te{te}*numstacks_*"),
    "subj_10_23_2025": ("/home/ajoshi/project2_ajoshi_27/data/disc_mri/scan_10_23_2025/outsvr", "svr_te{te}*numstacks_*"),
    "subj_12_03_2025": ("/home/ajoshi/project2_ajoshi_27/data/disc_mri/scan_12_03_2025/outsvr", "svr_te{te}*numstacks_*"),
    "subj_1_8_2026": ("/home/ajoshi/project2_ajoshi_27/data/disc_mri/scan_1_8_2026/outsvr", "svr_te{te}*numstacks_*"),
    "subj_2_6_2026": ("/home/ajoshi/project2_ajoshi_27/data/disc_mri/scan_2_6_2026/outsvr", "svr_te{te}*numstacks_*"),
    "subj_2_9_2026": ("/home/ajoshi/project2_ajoshi_27/data/disc_mri/scan_2_9_2026/outsvr", "svr_te{te}*numstacks_*"),
}

CACHE_DIR = "/home/ajoshi/Projects/disc_mri/fetal_mri/atlas_registrations"

def calculate_tissue_metrics(image_data, tissue_data):
    GM_LABELS = [112, 113]  
    WM_LABELS = [114, 115, 116, 117, 118, 119, 122, 123]  
    gm_mask = np.isin(tissue_data, GM_LABELS)
    wm_mask = np.isin(tissue_data, WM_LABELS)
    if np.sum(gm_mask) == 0 or np.sum(wm_mask) == 0: return np.nan, np.nan, np.nan, np.nan
    gm_mean = np.mean(image_data[gm_mask])
    wm_mean = np.mean(image_data[wm_mask])
    gm_std = np.std(image_data[gm_mask])
    wm_std = np.std(image_data[wm_mask])
    contrast_ratio = gm_mean / wm_mean if wm_mean != 0 else np.nan
    cnr = abs(wm_mean - gm_mean) / np.sqrt((wm_std**2 + gm_std**2) / 2)
    snr_gm = gm_mean / gm_std if gm_std != 0 else np.nan
    snr_wm = wm_mean / wm_std if wm_std != 0 else np.nan
    return contrast_ratio, cnr, snr_gm, snr_wm

def main():
    te = 98
    print(f"Ranking subjects at TE {te}, Max Stacks...")
    results = {}
    for subj_name, (d, pat_template) in SUBJECTS.items():
        pat = pat_template.format(te=te)
        all_files = glob.glob(os.path.join(d, pat + ".nii.gz"))
        native_files = [f for f in all_files if not f.endswith("_aligned.nii.gz")]
        
        parsed = []
        for f in native_files:
            m = re.search(r'numstacks_(\d+)_(?:iter_)?(\d+)', os.path.basename(f))
            if m:
                stacks, it = int(m.group(1)), int(m.group(2))
                parsed.append((stacks, it, f))
        
        if not parsed:
            continue
            
        stacks_dict = {}
        for stacks, it, f in parsed:
            if stacks not in stacks_dict:
                stacks_dict[stacks] = []
            stacks_dict[stacks].append((it, f))
            
        if not stacks_dict: continue
        
        max_stacks = max(stacks_dict.keys())
        stacks_dict[max_stacks].sort(key=lambda x: x[0], reverse=True)
        ref_path = stacks_dict[max_stacks][0][1]
        
        tissue_path = os.path.join(CACHE_DIR, f"{subj_name}_te{te}_tissue_reg.nii.gz")
        if not os.path.exists(tissue_path):
            continue
            
        img_data = nib.load(ref_path).get_fdata()
        tissue_mask = nib.load(tissue_path).get_fdata()
        
        cr, cnr, s_gm, s_wm = calculate_tissue_metrics(img_data, tissue_mask)
        
        results[subj_name] = {'CR': cr, 'CNR': cnr, 'SNR_WM': s_wm, 'max_stacks': max_stacks}
        print(f"{subj_name}: CR={cr:.3f}, CNR={cnr:.3f}, Max_Stacks={max_stacks}")

    print("\n--- Sorted by CR (Contrast Ratio) ---")
    for s in sorted(results.items(), key=lambda x: x[1]['CR'], reverse=True):
        print(f"{s[0]}: {s[1]}")

main()
