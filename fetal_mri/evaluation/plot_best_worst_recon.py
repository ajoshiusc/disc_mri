#!/usr/bin/env python3

"""
Script to identify and plot the best and worst subjects for a specific reconstruction
parameter set (6 stacks, TE=140ms) based on SSIM against their respective reference.
Uses nilearn.plotting.plot_anat to visualize the results.
"""

import os
import glob
import re
import numpy as np
import nibabel as nib
import matplotlib.pyplot as plt
from nilearn import plotting
from evaluation.comprehensive_te_analysis import get_tissue_mask_in_native_space, calculate_tissue_metrics

# The 10 subjects used in the analysis
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

TARGET_TE = 140
TARGET_STACKS = 6

def get_subject_files(d, pat_template, te):
    pat = pat_template.format(te=te)
    all_files = glob.glob(os.path.join(d, pat + ".nii.gz"))
    native_files = [f for f in all_files if not f.endswith("_aligned.nii.gz")]
    
    parsed = []
    for f in native_files:
        m = re.search(r'numstacks_(\d+)_(?:iter_)?(\d+)', os.path.basename(f))
        if m:
            stacks, it = int(m.group(1)), int(m.group(2))
            parsed.append((stacks, it, f))
            
    final_dict = {}
    for stacks, it, f in parsed:
        if stacks not in final_dict:
            final_dict[stacks] = []
        final_dict[stacks].append(f)
    return final_dict

def calculate_ssim(img_data, ref_data):
    if img_data.shape != ref_data.shape:
        return np.nan
        
    img_vol = np.expand_dims(img_data, axis=(0, 1))
    ref_vol = np.expand_dims(ref_data, axis=(0, 1))
    t_img = torch.tensor(img_vol, dtype=torch.float32)
    t_ref = torch.tensor(ref_vol, dtype=torch.float32)
    
    img_valid = t_img[t_img > 0]
    ref_valid = t_ref[t_ref > 0]
    if len(img_valid) == 0 or len(ref_valid) == 0:
        return np.nan
        
    img_max, img_min = img_valid.max(), img_valid.min()
    ref_max, ref_min = ref_valid.max(), ref_valid.min()
    
    t_img_norm = (t_img - img_min) / (img_max - img_min + 1e-8)
    t_ref_norm = (t_ref - ref_min) / (ref_max - ref_min + 1e-8)
    
    ssim_loss = SSIMLoss(spatial_dims=3)(t_img_norm, t_ref_norm)
    return 1 - ssim_loss.item()

def main():
    print(f"Finding best and worst subjects for TE={TARGET_TE}ms, {TARGET_STACKS} stacks based on Mean SNR (WM & GM)...")
    
    subject_scores = {}
    
    for subj_name, (d, pat) in SUBJECTS.items():
        stack_files = get_subject_files(d, pat, TARGET_TE)
        if not stack_files or TARGET_STACKS not in stack_files:
            print(f"Skipping {subj_name}: target stacks not found.")
            continue
            
        max_stacks = max(stack_files.keys())
        ref_path = stack_files[max_stacks][0]
        
        # Take the first reconstruction of the target stacks
        target_path = stack_files[TARGET_STACKS][0]
        
        try:
            img_data = nib.load(target_path).get_fdata()
            tissue_mask = get_tissue_mask_in_native_space(subj_name, TARGET_TE, ref_path)
            cr, cnr, snr_gm, snr_wm = calculate_tissue_metrics(img_data, tissue_mask)
            
            # Combine GM and WM SNR for an overall SNR score
            score = (snr_gm + snr_wm) / 2.0
            
            if not np.isnan(score):
                subject_scores[subj_name] = {
                    'score': score,
                    'file': target_path,
                    'ref_file': ref_path,
                    'snr_gm': snr_gm,
                    'snr_wm': snr_wm
                }
                print(f"  {subj_name}: Mean SNR = {score:.4f} (WM={snr_wm:.4f}, GM={snr_gm:.4f})")
        except Exception as e:
            print(f"Error processing {subj_name}: {e}")
            
    if not subject_scores:
        print("No valid data found to compare.")
        return

    # Sort to find best and worst
    sorted_subjects = sorted(subject_scores.items(), key=lambda x: x[1]['score'])
    worst_subj, worst_data = sorted_subjects[0]
    best_subj, best_data = sorted_subjects[-1]

    print(f"\nWorst: {worst_subj} (Mean SNR: {worst_data['score']:.4f})")
    print(f"Best:  {best_subj} (Mean SNR: {best_data['score']:.4f})")
    
    CACHE_DIR = "/home/ajoshi/Projects/disc_mri/fetal_mri/atlas_registrations"
    os.makedirs(CACHE_DIR, exist_ok=True)
    ATLAS_PATH = "/deneb_disk/disc_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA30.nii.gz"
    
    # Process Best Subject - Direct registration to Atlas with center of mass initializer
    print("Aligning Best Subject directly to Atlas (12 DOF, corratio cost, cor initializer)...")
    best_aligned_path = os.path.join(CACHE_DIR, f"{best_subj}_te140_6stacks_aligned_direct.nii.gz")
    best_mat_direct = os.path.join(CACHE_DIR, f"{best_subj}_te140_6stacks_reg_direct.mat") 
    os.system(f"flirt -in {best_data['file']} -ref {ATLAS_PATH} -omat {best_mat_direct} -out {best_aligned_path} -usesqform -searchrx -180 180 -searchry -180 180 -searchrz -180 180 -dof 9 -cost mutualinfo -interp trilinear")
    
    # Process Worst Subject - Direct registration to Atlas with center of mass initializer
    print("Aligning Worst Subject directly to Atlas (12 DOF, corratio cost, cor initializer)...")
    worst_aligned_path = os.path.join(CACHE_DIR, f"{worst_subj}_te140_6stacks_aligned_direct.nii.gz")
    worst_mat_direct = os.path.join(CACHE_DIR, f"{worst_subj}_te140_6stacks_reg_direct.mat")
    os.system(f"flirt -in {worst_data['file']} -ref {ATLAS_PATH} -omat {worst_mat_direct} -out {worst_aligned_path} -usesqform -searchrx -180 180 -searchry -180 180 -searchrz -180 180 -dof 9 -cost mutualinfo ")

    '''cmd = (
        "flirt -in "
        + outsvr
        + " -ref "
        + fetal_atlas
        + " -out "
        + outsvr_aligned
        + " -dof 6 -omat "
        + f"reorient_te{te}.mat"
        + " -searchrx -180 180 -searchry -180 180 -searchrz -180 180 -cost mutualinfo"
    )'''
    print("\nGenerating plots... This may take a moment.")
    fig = plt.figure(figsize=(12, 10))
    
    ax1 = fig.add_subplot(211)
    title_best = f"BEST Subject ({best_subj})\nTE {TARGET_TE}ms | {TARGET_STACKS} Stacks | Mean SNR: {best_data['score']:.2f} (WM:{best_data['snr_wm']:.2f}, GM:{best_data['snr_gm']:.2f})"
    plotting.plot_anat(best_aligned_path, axes=ax1,
                       title=title_best,
                       display_mode='ortho', dim=-1, annotate=True, draw_cross=False)
                       
    ax2 = fig.add_subplot(212)
    title_worst = f"WORST Subject ({worst_subj})\nTE {TARGET_TE}ms | {TARGET_STACKS} Stacks | Mean SNR: {worst_data['score']:.2f} (WM:{worst_data['snr_wm']:.2f}, GM:{worst_data['snr_gm']:.2f})"
    plotting.plot_anat(worst_aligned_path, axes=ax2,
                       title=title_worst,
                       display_mode='ortho', dim=-1, annotate=True, draw_cross=False)

    plt.tight_layout()
    out_file = "best_worst_recon_snr_te140_6stacks.png"
    plt.savefig(out_file, dpi=300, bbox_inches='tight')
    print(f"Saved figure to {out_file}")

if __name__ == "__main__":
    main()
