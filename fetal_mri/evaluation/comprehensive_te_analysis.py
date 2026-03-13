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
    "subj_8_11_2023": 30,         # TODO: Update with actual gestational age
    "subj_9_12_2023": 30,         # TODO: Update with actual gestational age
    "subj_11_3_2023_babya": 30,   # TODO: Update with actual gestational age
    "subj_11_3_2023_babyb": 30,   # TODO: Update with actual gestational age
    "subj_3_20_2024": 30,         # TODO: Update with actual gestational age
    "subj_10_23_2025": 30,        # TODO: Update with actual gestational age
    "subj_12_03_2025": 30,        # TODO: Update with actual gestational age
    "subj_1_8_2026": 30,          # TODO: Update with actual gestational age
    "subj_2_6_2026": 30,          # TODO: Update with actual gestational age
    "subj_2_9_2026": 30,          # TODO: Update with actual gestational age
}

FETAL_ATLAS_DIR = "/deneb_disk/disc_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3"
CACHE_DIR = "/home/ajoshi/Projects/disc_mri/fetal_mri/atlas_registrations"
os.makedirs(CACHE_DIR, exist_ok=True)

TE_VALUES = [98, 140, 181, 272]

def get_subject_files(d, pat_template, te):
    pat = pat_template.format(te=te)
    all_files = glob.glob(os.path.join(d, pat + ".nii.gz"))
    # Filter out _aligned to avoid mixing spaces if we do native analysis
    native_files = [f for f in all_files if not f.endswith("_aligned.nii.gz")]
    
    parsed = []
    for f in native_files:
        # Regex to capture numstacks and iter gracefully
        m = re.search(r'numstacks_(\d+)_(?:iter_)?(\d+)', os.path.basename(f))
        if m:
            stacks, it = int(m.group(1)), int(m.group(2))
            parsed.append((stacks, it, f))
    
    if not parsed:
        return {}
    
    # Keep all iterations (combinations) per stack
    final_dict = {}
    for stacks, it, f in parsed:
        if stacks not in final_dict:
            final_dict[stacks] = []
        final_dict[stacks].append(f)
        
    return final_dict

def get_tissue_mask_for_subject(subj_name):
    # Retrieve the GA for the subject, default to 30 if not found
    ga = SUBJECT_GA.get(subj_name, 30)
    
    # Construct the path to the tissue atlas for this gestational age
    tissue_path = os.path.join(FETAL_ATLAS_DIR, f"STA{ga}_tissue.nii.gz")
    
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
    
    t_img_norm = (t_img - img_min) / (img_max - img_min + 1e-8)
    t_ref_norm = (t_ref - ref_min) / (ref_max - ref_min + 1e-8)
    
    ssim_loss = SSIMLoss(spatial_dims=3)(t_img_norm, t_ref_norm)
    ssim = 1 - ssim_loss.item()
    
    nmse_loss = MSELoss()(t_img_norm, t_ref_norm) / (t_ref_norm ** 2).mean()
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
    
    for subj_name, (d, pat) in tqdm(SUBJECTS.items(), desc="Subjects"):
        ga = SUBJECT_GA.get(subj_name, 30)
        atlas_path = os.path.join(FETAL_ATLAS_DIR, f"STA{ga}.nii.gz")
        
        for te in TE_VALUES:
            stack_files = get_subject_files(d, pat, te)
            if not stack_files:
                continue
                
            max_stacks = max(stack_files.keys())
            # stack_files contains lists now, use the first one from max_stacks as reference geometric target
            ref_path = stack_files[max_stacks][0]
            try:
                ref_aligned_name = f"{subj_name}_te{te}_ref_aligned.nii.gz"
                ref_mat_name = f"{subj_name}_te{te}_ref.mat"
                
                ref_aligned_path = os.path.join(CACHE_DIR, ref_aligned_name)
                ref_mat_path = os.path.join(CACHE_DIR, ref_mat_name)
                
                if not os.path.exists(ref_aligned_path):
                    print(f"  [FLIRT] Computing base alignment for {subj_name} TE {te}...")
                    cmd = f"flirt -in {ref_path} -ref {atlas_path} -omat {ref_mat_path} -out {ref_aligned_path} -dof 6 -searchrx -180 180 -searchry -180 180 -searchrz -180 180 -cost normmi"
                    subprocess.run(cmd, shell=True, check=True, stdout=subprocess.DEVNULL)
                
                ref_data = nib.load(ref_aligned_path).get_fdata()
                tissue_mask = get_tissue_mask_for_subject(subj_name)
            except Exception as e:
                print(f"Skipping {subj_name} TE {te} due to error: {e}")
                continue
                
            for stacks, fpath_list in stack_files.items():
                if stacks not in all_subject_data[te]:
                    all_subject_data[te][stacks] = {'cr':[], 'cnr':[], 'snr_gm':[], 'snr_wm':[], 'ssim':[], 'nmse':[]}
                
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
                        
                        all_subject_data[te][stacks]['cr'].append(cr)
                        all_subject_data[te][stacks]['cnr'].append(cnr)
                        all_subject_data[te][stacks]['snr_gm'].append(s_gm)
                        all_subject_data[te][stacks]['snr_wm'].append(s_wm)
                        all_subject_data[te][stacks]['ssim'].append(ssim)
                        all_subject_data[te][stacks]['nmse'].append(nmse)
                    except Exception as e:
                        pass
                    
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
        valid_stacks = sorted([s for s in all_subject_data[te].keys() if s >= 1 and s <= 12])
        if not valid_stacks:
            continue
            
        c, m = colors[idx], markers[idx]
        
        for key, title, ax, is_log in metrics:
            means = [np.nanmean(all_subject_data[te][s][key]) for s in valid_stacks]
            errs = [np.nanstd(all_subject_data[te][s][key]) for s in valid_stacks]
            
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
    
    save_outputs(all_subject_data)
    print(f"Finished! Output saved to {fig_path}")

import json
def save_outputs(all_subject_data):
    with open("comprehensive_te_analysis_results.txt", "w") as f:
        f.write("COMPREHENSIVE FETAL MRI IMAGE QUALITY ANALYSIS (10 SUBJECT AVERAGE)\n")
        f.write("="*60 + "\n\n")
        f.write("Metrics computed for each TE and stack number:\n")
        f.write("- Contrast Ratio (CR): WM/GM signal ratio\n")
        f.write("- Contrast-to-Noise Ratio (CNR): tissue contrast relative to noise\n")
        f.write("- SNR GM/WM: signal-to-noise ratios for gray/white matter\n")
        f.write("- SSIM: structural similarity index (vs. maximum stacks)\n")
        f.write("- NMSE: mean squared error (vs. maximum stacks)\n\n")
        
        for te in [98, 140, 181, 272]:
            f.write(f"TE {te} ms:\n")
            f.write("Stack\tCR\tCNR\tSNR_GM\tSNR_WM\tSSIM\tNMSE\n")
            f.write("-" * 60 + "\n")
            
            valid_stacks = sorted([s for s in all_subject_data[te].keys() if 1 <= s <= 12])
            for s in valid_stacks:
                mean_cr = np.nanmean(all_subject_data[te][s]['cr'])
                mean_cnr = np.nanmean(all_subject_data[te][s]['cnr'])
                mean_snr_gm = np.nanmean(all_subject_data[te][s]['snr_gm'])
                mean_snr_wm = np.nanmean(all_subject_data[te][s]['snr_wm'])
                mean_ssim = np.nanmean(all_subject_data[te][s]['ssim'])
                mean_nmse = np.nanmean(all_subject_data[te][s]['nmse'])
                f.write(f"{s}\t{mean_cr:.3f}\t{mean_cnr:.3f}\t{mean_snr_gm:.3f}\t{mean_snr_wm:.3f}\t{mean_ssim:.3f}\t{mean_nmse:.2e}\n")
            f.write("\n")
            
    json_data = {}
    for te in [98, 140, 181, 272]:
        json_data[str(te)] = {}
        valid_stacks = sorted([s for s in all_subject_data[te].keys() if 1 <= s <= 12])
        for s in valid_stacks:
            cr = all_subject_data[te][s]['cr']
            cnr = all_subject_data[te][s]['cnr']
            snr_gm = all_subject_data[te][s]['snr_gm']
            snr_wm = all_subject_data[te][s]['snr_wm']
            ssim = [val for val in all_subject_data[te][s]['ssim'] if not np.isnan(val)]
            nmse = [val for val in all_subject_data[te][s]['nmse'] if not np.isnan(val)]
            
            json_data[str(te)][str(s)] = {
                "cr_mean": float(np.nanmean(cr)), "cr_std": float(np.nanstd(cr)),
                "cnr_mean": float(np.nanmean(cnr)), "cnr_std": float(np.nanstd(cnr)),
                "snr_gm_mean": float(np.nanmean(snr_gm)), "snr_gm_std": float(np.nanstd(snr_gm)),
                "snr_wm_mean": float(np.nanmean(snr_wm)), "snr_wm_std": float(np.nanstd(snr_wm)),
                "ssim_mean": float(np.nanmean(ssim)) if ssim else 1.0, "ssim_std": float(np.nanstd(ssim)) if ssim else 0.0,
                "nmse_mean": float(np.nanmean(nmse)) if nmse else 0.0, "nmse_std": float(np.nanstd(nmse)) if nmse else 0.0
            }
            
    with open("real_error_bar_data.json", "w") as f:
        json.dump(json_data, f, indent=2)


if __name__ == "__main__":
    main()
