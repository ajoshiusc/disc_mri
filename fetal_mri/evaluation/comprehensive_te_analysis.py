#!/usr/bin/env python3

"""
Comprehensive Fetal MRI Analysis (Multi-Subject)
Evaluates image quality metrics vs TE and input stacks across 10 subjects.
Generates metrics by dynamically aligning the fetal atlas to the native SVR space of each subject.
"""

import os
import glob
import re
import numpy as np
import nibabel as nib
import matplotlib.pyplot as plt
from tqdm import tqdm
import torch
import subprocess
from monai.losses.ssim_loss import SSIMLoss  
from torch.nn import MSELoss

# Professional plot parameters
plt.rcParams.update({
    'font.size': 12, 'axes.titlesize': 14, 'axes.labelsize': 12,
    'xtick.labelsize': 11, 'ytick.labelsize': 11, 'legend.fontsize': 10,
    'figure.titlesize': 16, 'font.family': 'DejaVu Sans',
    'axes.linewidth': 1.5, 'grid.linewidth': 0.8,
    'lines.linewidth': 2.0, 'lines.markersize': 8
})

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

SUBJECT_GA = {
    "subj_8_11_2023": 30,         
    "subj_9_12_2023": 37,         
    "subj_11_3_2023_babya": 30,   
    "subj_11_3_2023_babyb": 30,   
    "subj_3_20_2024": 24,         
    "subj_10_23_2025": 38,        
    "subj_12_03_2025": 29,        
    "subj_1_8_2026": 36,          
    "subj_2_6_2026": 37,          
    "subj_2_9_2026": 35,          
}

FETAL_ATLAS_DIR = "/deneb_disk/disc_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3"
CACHE_DIR = "/home/ajoshi/Projects/disc_mri/fetal_mri/atlas_registrations"
os.makedirs(CACHE_DIR, exist_ok=True)

# Configuration
OUTLIER_REJECTION_RATE = 0.4
TE_VALUES = [98, 140, 181, 272]
# Minimum number of consecutive (step-1) stack counts a subject must have to be included.
# Subjects with sparse/gapped sequences like [3,6,9] are excluded.
MIN_CONSECUTIVE_STACKS = 4

def has_consecutive_stacks(stack_keys):
    """Return True only if the sorted stack counts form a gap-free consecutive sequence
    of length >= MIN_CONSECUTIVE_STACKS (step 1 between every adjacent pair)."""
    s = sorted(stack_keys)
    if len(s) < MIN_CONSECUTIVE_STACKS:
        return False
    for i in range(1, len(s)):
        if s[i] - s[i-1] != 1:
            return False
    return True

def get_subject_files(d, pat_template, te):
    pat = pat_template.format(te=te)
    all_files = glob.glob(os.path.join(d, pat + ".nii.gz"))
    # Filter out _aligned to avoid mixing spaces if we do native analysis
    native_files = [f for f in all_files if not f.endswith("_aligned.nii.gz")]
    
    parsed = []
    for f in native_files:
        # Regex to capture numstacks and iter gracefully
        bname = os.path.basename(f)
        m = re.search(r'numstacks_(\d+)', bname)
        if m:
            stacks = int(m.group(1))
            it_m = re.search(r'iter_(\d+)', bname)
            it = int(it_m.group(1)) if it_m else 0
            parsed.append((stacks, it, f))
    
    if not parsed:
        return {}
    
    # Group by stack
    stack_dict = {}
    for stacks, it, f in parsed:
        if stacks not in stack_dict:
            stack_dict[stacks] = []
        stack_dict[stacks].append(f)
        
    return stack_dict

def get_tissue_mask_for_subject(subj_name):
    # Retrieve the GA for the subject, default to 30 if not found
    ga = SUBJECT_GA.get(subj_name, 30)
    ga_str = f"{ga}exp" if ga >= 36 else str(ga)
    
    # Construct the path to the tissue atlas for this gestational age
    tissue_path = os.path.join(FETAL_ATLAS_DIR, f"STA{ga_str}_tissue.nii.gz")
    
    if not os.path.exists(tissue_path):
        raise FileNotFoundError(f"Missing tissue atlas for GA {ga}: {tissue_path}")
        
    return nib.load(tissue_path).get_fdata()

def calculate_ssim_nmse(img_data, ref_data):
    if img_data.shape != ref_data.shape:
        return np.nan, np.nan
        
    img_vol = np.expand_dims(img_data, axis=(0, 1))
    ref_vol = np.expand_dims(ref_data, axis=(0, 1))
    t_img = torch.tensor(img_vol, dtype=torch.float32)
    t_ref = torch.tensor(ref_vol, dtype=torch.float32)
    
    # Normalize for SSIM
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
    
    ssim_loss = SSIMLoss(spatial_dims=3)(t_img_norm, t_ref_norm)
    ssim = 1 - ssim_loss.item()
    
    nmse_loss = MSELoss()(t_img_norm, t_ref_norm) / ((t_ref_norm ** 2).mean() + 1e-8)
    nmse = nmse_loss.item()
     
    return ssim, nmse

def calculate_tissue_metrics(img_data, tissue_data):
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
    
    cr = mu_gm / mu_wm if mu_wm > 0 else np.nan
    cnr = abs(mu_wm - mu_gm) / np.sqrt((sig_wm**2 + sig_gm**2)/2) if (sig_wm>0 or sig_gm>0) else np.nan
    snr_gm = mu_gm / sig_gm if sig_gm > 0 else np.nan
    snr_wm = mu_wm / sig_wm if sig_wm > 0 else np.nan
    
    return cr, cnr, snr_gm, snr_wm

def main():
    print("Starting Comprehensive Inter-Subject Analysis...")
    all_subject_data = {te: {} for te in TE_VALUES}
    
    # --- PHASE 1: Registrations ---
    print("Phase 1: Computing all registrations...")
    for subj_name, (d, pat) in tqdm(SUBJECTS.items(), desc="Registrations"):
        ga = SUBJECT_GA.get(subj_name, 30)
        ga_str = f"{ga}exp" if ga >= 36 else str(ga)
        atlas_path = os.path.join(FETAL_ATLAS_DIR, f"STA{ga_str}.nii.gz")
        
        for te in TE_VALUES:
            stack_files = get_subject_files(d, pat, te)
            if not stack_files:
                continue

            if not has_consecutive_stacks(stack_files.keys()):
                print(f"  [SKIP] {subj_name} TE {te}: stacks {sorted(stack_files.keys())} are not consecutive with step 1")
                continue
                
            max_stacks = max(stack_files.keys())
            # stack_files contains lists now, use the first one from max_stacks as reference geometric target
            ref_path = stack_files[max_stacks][0]
            
            ref_aligned_name = f"{subj_name}_te{te}_ref_aligned.nii.gz"
            ref_mat_name = f"{subj_name}_te{te}_ref.mat"
            
            ref_aligned_path = os.path.join(CACHE_DIR, ref_aligned_name)
            ref_mat_path = os.path.join(CACHE_DIR, ref_mat_name)
            
            if not os.path.exists(ref_aligned_path):
                print(f"  [FLIRT] Computing base alignment for {subj_name} TE {te}...")
                cmd = f"flirt -in {ref_path} -ref {atlas_path} -omat {ref_mat_path} -out {ref_aligned_path} -dof 6 -searchrx -180 180 -searchry -180 180 -searchrz -180 180 -cost normmi"
                subprocess.run(cmd, shell=True, check=True, stdout=subprocess.DEVNULL)


    # --- PHASE 2: Apply XFM and Extract Metrics ---
    print("Phase 2: Applying registrations and extracting metrics...")
    for subj_name, (d, pat) in tqdm(SUBJECTS.items(), desc="Metrics"):
        ga = SUBJECT_GA.get(subj_name, 30)
        ga_str = f"{ga}exp" if ga >= 36 else str(ga)
        atlas_path = os.path.join(FETAL_ATLAS_DIR, f"STA{ga_str}.nii.gz")
        
        for te in TE_VALUES:
            stack_files = get_subject_files(d, pat, te)
            if not stack_files:
                continue

            if not has_consecutive_stacks(stack_files.keys()):
                continue

            ref_aligned_name = f"{subj_name}_te{te}_ref_aligned.nii.gz"
            ref_mat_name = f"{subj_name}_te{te}_ref.mat"
            
            ref_aligned_path = os.path.join(CACHE_DIR, ref_aligned_name)
            ref_mat_path = os.path.join(CACHE_DIR, ref_mat_name)
            
            if not os.path.exists(ref_aligned_path):
                continue
                
            try:
                ref_data = nib.load(ref_aligned_path).get_fdata()
                tissue_mask = get_tissue_mask_for_subject(subj_name)
            except Exception as e:
                print(f"Skipping {subj_name} TE {te} due to error: {e}")
                continue
                
            for stacks, fpath_list in stack_files.items():
                if stacks not in all_subject_data[te]:
                    all_subject_data[te][stacks] = {}
                if subj_name not in all_subject_data[te][stacks]:
                    all_subject_data[te][stacks][subj_name] = {'cr':[], 'cnr':[], 'snr_gm':[], 'snr_wm':[], 'ssim':[], 'nmse':[]}
                
                print(f"Processing TE {te}, Stacks {stacks}, Combinations: {len(fpath_list)}")
                for fpath in fpath_list:
                    try:
                        bname = os.path.basename(fpath).replace(".nii.gz", "")
                        out_aligned = os.path.join(CACHE_DIR, f"{subj_name}_{bname}_aligned.nii.gz")
                        
                        if not os.path.exists(out_aligned):
                            cmd = f"flirt -in {fpath} -ref {atlas_path} -out {out_aligned} -applyxfm -init {ref_mat_path}"
                            subprocess.run(cmd, shell=True, check=True, stdout=subprocess.DEVNULL)
                            
                        img_data = nib.load(out_aligned).get_fdata()
                        
                        cr, cnr, s_gm, s_wm = calculate_tissue_metrics(img_data, tissue_mask)
                        ssim, nmse = calculate_ssim_nmse(img_data, ref_data)
                        
                        all_subject_data[te][stacks][subj_name]['cr'].append(cr)
                        all_subject_data[te][stacks][subj_name]['cnr'].append(cnr)
                        all_subject_data[te][stacks][subj_name]['snr_gm'].append(s_gm)
                        all_subject_data[te][stacks][subj_name]['snr_wm'].append(s_wm)
                        all_subject_data[te][stacks][subj_name]['ssim'].append(ssim)
                        all_subject_data[te][stacks][subj_name]['nmse'].append(nmse)
                    except Exception as e:
                        pass
                    
    # Reject OUTLIER_REJECTION_RATE worst data per subject as outliers, and calculate subject means
    aggregated_data_dict = {te: {} for te in TE_VALUES}
    for te in all_subject_data:
        for s in all_subject_data[te]:
            aggregated_data_dict[te][s] = {'cr':[], 'cnr':[], 'snr_gm':[], 'snr_wm':[], 'ssim':[], 'nmse':[]}
            for subj in all_subject_data[te][s]:
                for metric in ['cr', 'cnr', 'snr_gm', 'snr_wm', 'ssim', 'nmse']:
                    values = all_subject_data[te][s][subj][metric]
                    valid = [v for v in values if not np.isnan(v)]
                    if not valid: continue
                    
                    # Keep top percentage of reconstructions for this subject
                    n_keep = max(1, int(len(valid) * (1.0 - OUTLIER_REJECTION_RATE)))
                    
                    if metric == 'nmse':
                        # Lower is better, so worst X% are highest values
                        filtered = sorted(valid)[:n_keep]
                    else:
                        # Higher is better, so worst X% are lowest values
                        filtered = sorted(valid, reverse=True)[:n_keep]
                        
                    # Store only the mean of the valid iterations for the subject to correctly compute inter-subject variance
                    subj_mean = np.nanmean(filtered)
                    aggregated_data_dict[te][s][metric].append(subj_mean)
                    
    # From here on, 'final_data' uses the inter-subject aggregated format 
    final_data = aggregated_data_dict

    # Generate Output Means
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('Comprehensive Image Quality Assessment: 10 Subject Average', fontsize=18, fontweight='bold', y=0.98)
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    markers = ['o', 's', '^', 'd']
    metrics = [
        ('cr', 'Contrast Ratio (GM/WM)', axes[0,0], False),
        ('cnr', 'CNR (GM vs WM)', axes[0,1], False),
        ('ssim', 'Structural Similarity Index (SSIM)', axes[0,2], False),
        ('snr_gm', 'SNR Gray Matter', axes[1,0], False),
        ('snr_wm', 'SNR White Matter', axes[1,1], False),
        ('nmse', 'Mean Squared Error (NMSE)', axes[1,2], True)
    ]
    
    for ax in axes.flat:
        ax.grid(True, linestyle='--', alpha=0.7)
        
    for idx, te in enumerate(TE_VALUES):
        # Gather available stacks
        valid_stacks = sorted([s for s in final_data[te].keys() if s >= 1 and s <= 12])
        if not valid_stacks:
            continue
            
        c, m = colors[idx], markers[idx]
        
        for key, title, ax, is_log in metrics:
            means, errs = [], []
            for s in valid_stacks:
                subj_means = [val for val in final_data[te][s][key] if not np.isnan(val)]
                if not subj_means:
                    means.append(np.nan)
                    errs.append(0.0)
                else:
                    n = len(subj_means)
                    means.append(np.nanmean(subj_means))
                    errs.append(np.nanstd(subj_means, ddof=1) / np.sqrt(n) if n > 1 else 0.0)

            ax.errorbar(valid_stacks, means, yerr=errs, fmt=m+'-', color=c,
                        label=f'TE {te} ms', capsize=4, capthick=1.5, elinewidth=1.5)
            ax.set_title(title, fontweight='bold')
            ax.set_xlabel('Number of Input Stacks')
            if is_log:
                ax.set_yscale('log')
                
    for key, title, ax, is_log in metrics:
        ax.legend(loc='best')
        ax.set_xticks(range(1, 13))
        
    plt.tight_layout(rect=(0, 0, 1, 0.96))
    fig_path = os.path.join("/home/ajoshi/Projects/disc_mri/fetal_mri", "comprehensive_te_analysis_10subjects.png")
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    
    save_outputs(final_data)
    print(f"Finished! Output saved to {fig_path}")

import json
from typing import Dict, List

def save_outputs(final_data: Dict[int, Dict[int, Dict[str, List[float]]]]):
    with open("comprehensive_te_analysis_results.txt", "w") as f:
        f.write("COMPREHENSIVE FETAL MRI IMAGE QUALITY ANALYSIS (10 SUBJECT AVERAGE)\n")
        f.write("="*60 + "\n\n")
        f.write("Metrics computed for each TE and stack number:\n")
        f.write("- Contrast Ratio (CR): GM/WM signal ratio\n")
        f.write("- Contrast-to-Noise Ratio (CNR): tissue contrast relative to noise\n")
        f.write("- SNR GM/WM: signal-to-noise ratios for gray/white matter\n")
        f.write("- SSIM: structural similarity index (vs. maximum stacks)\n")
        f.write("- NMSE: mean squared error (vs. maximum stacks)\n\n")
        
        for te in [98, 140, 181, 272]:
            f.write(f"TE {te} ms:\n")
            f.write("Stack\tCR\tCNR\tSNR_GM\tSNR_WM\tSSIM\tNMSE\n")
            f.write("-" * 60 + "\n")
            
            valid_stacks = sorted([s for s in final_data[te].keys() if 1 <= s <= 12])
            for s in valid_stacks:
                cr_vals = [v for v in final_data[te][s]['cr'] if not np.isnan(v)]
                cnr_vals = [v for v in final_data[te][s]['cnr'] if not np.isnan(v)]
                snr_gm_vals = [v for v in final_data[te][s]['snr_gm'] if not np.isnan(v)]
                snr_wm_vals = [v for v in final_data[te][s]['snr_wm'] if not np.isnan(v)]
                ssim_vals = [v for v in final_data[te][s]['ssim'] if not np.isnan(v)]
                nmse_vals = [v for v in final_data[te][s]['nmse'] if not np.isnan(v)]
                
                mean_cr = np.nanmean(cr_vals) if cr_vals else np.nan
                mean_cnr = np.nanmean(cnr_vals) if cnr_vals else np.nan
                mean_snr_gm = np.nanmean(snr_gm_vals) if snr_gm_vals else np.nan
                mean_snr_wm = np.nanmean(snr_wm_vals) if snr_wm_vals else np.nan
                mean_ssim = np.nanmean(ssim_vals) if ssim_vals else np.nan
                mean_nmse = np.nanmean(nmse_vals) if nmse_vals else np.nan
                f.write(f"{s}\t{mean_cr:.3f}\t{mean_cnr:.3f}\t{mean_snr_gm:.3f}\t{mean_snr_wm:.3f}\t{mean_ssim:.3f}\t{mean_nmse:.2e}\n")
            f.write("\n")
            
    json_data = {}
    for te in [98, 140, 181, 272]:
        json_data[str(te)] = {}
        valid_stacks = sorted([s for s in final_data[te].keys() if 1 <= s <= 12])
        for s in valid_stacks:
            cr = [val for val in final_data[te][s]['cr'] if not np.isnan(val)]
            cnr = [val for val in final_data[te][s]['cnr'] if not np.isnan(val)]
            snr_gm = [val for val in final_data[te][s]['snr_gm'] if not np.isnan(val)]
            snr_wm = [val for val in final_data[te][s]['snr_wm'] if not np.isnan(val)]
            ssim = [val for val in final_data[te][s]['ssim'] if not np.isnan(val)]
            nmse = [val for val in final_data[te][s]['nmse'] if not np.isnan(val)]
            
            json_data[str(te)][str(s)] = {
                "cr_mean": float(np.nanmean(cr)) if cr else 0.0, "cr_std": float(np.nanstd(cr, ddof=1) if len(cr) > 1 else 0.0),
                "cnr_mean": float(np.nanmean(cnr)) if cnr else 0.0, "cnr_std": float(np.nanstd(cnr, ddof=1) if len(cnr) > 1 else 0.0),
                "snr_gm_mean": float(np.nanmean(snr_gm)) if snr_gm else 0.0, "snr_gm_std": float(np.nanstd(snr_gm, ddof=1) if len(snr_gm) > 1 else 0.0),
                "snr_wm_mean": float(np.nanmean(snr_wm)) if snr_wm else 0.0, "snr_wm_std": float(np.nanstd(snr_wm, ddof=1) if len(snr_wm) > 1 else 0.0),
                "ssim_mean": float(np.nanmean(ssim)) if ssim else 1.0, "ssim_std": float(np.nanstd(ssim, ddof=1) if len(ssim) > 1 else 0.0),
                "nmse_mean": float(np.nanmean(nmse)) if nmse else 0.0, "nmse_std": float(np.nanstd(nmse, ddof=1) if len(nmse) > 1 else 0.0)
            }
            
    with open("real_error_bar_data.json", "w") as f:
        json.dump(json_data, f, indent=2)


if __name__ == "__main__":
    main()
