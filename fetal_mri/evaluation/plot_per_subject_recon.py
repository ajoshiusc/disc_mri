#!/usr/bin/env python3

"""
Create one PNG per subject showing the reconstruction (no text/colorbars).
"""

import os
import glob
import re
import numpy as np
import nibabel as nib
import matplotlib.pyplot as plt
from nilearn import plotting
from comprehensive_te_analysis import get_tissue_mask_for_subject, calculate_tissue_metrics

# Reuse same SUBJECTS/TARGET settings as existing script
SUBJECTS = {
    "subj_8_11_2023": ("/deneb_disk/disc_mri/scan_8_11_2023/outsvr", "svr_te{te}*numstacks_*") ,
    "subj_9_12_2023": ("/deneb_disk/disc_mri/scan_9_12_2023/outsvr", "svr_te{te}*numstacks_*") ,
    "subj_11_3_2023_babya": ("/deneb_disk/disc_mri/scan_11_3_2023_twins_nii_rot/outsvr", "svr_te{te}_babya*numstacks_*") ,
    "subj_11_3_2023_babyb": ("/deneb_disk/disc_mri/scan_11_3_2023_twins_nii_rot/outsvr", "svr_te{te}_babyb*numstacks_*") ,
    "subj_3_20_2024": ("/deneb_disk/disc_mri/scan_3_20_2024/outsvr", "svr_te{te}*numstacks_*") ,
    "subj_10_23_2025": ("/home/ajoshi/project2_ajoshi_27/data/disc_mri/scan_10_23_2025/outsvr", "svr_te{te}*numstacks_*") ,
    "subj_12_03_2025": ("/home/ajoshi/project2_ajoshi_27/data/disc_mri/scan_12_03_2025/outsvr", "svr_te{te}*numstacks_*") ,
    "subj_1_8_2026": ("/home/ajoshi/project2_ajoshi_27/data/disc_mri/scan_1_8_2026/outsvr", "svr_te{te}*numstacks_*") ,
    "subj_2_6_2026": ("/home/ajoshi/project2_ajoshi_27/data/disc_mri/scan_2_6_2026/outsvr", "svr_te{te}*numstacks_*") ,
    "subj_2_9_2026": ("/home/ajoshi/project2_ajoshi_27/data/disc_mri/scan_2_9_2026/outsvr", "svr_te{te}*numstacks_*") ,
}

TARGET_TE = 140
TARGET_STACKS = 12
CACHE_DIR = "/home/ajoshi/Projects/disc_mri/fetal_mri/atlas_registrations"
os.makedirs(CACHE_DIR, exist_ok=True)


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


def collect_subjects():
    subject_scores = {}
    for subj_name, (d, pat) in SUBJECTS.items():
        stack_files = get_subject_files(d, pat, TARGET_TE)
        if not stack_files or TARGET_STACKS not in stack_files:
            print(f"Skipping {subj_name}: target stacks not found.")
            continue
        target_path = stack_files[TARGET_STACKS][0]
        try:
            img_data = nib.load(target_path).get_fdata()
            vals = img_data[img_data > 0]
            if vals.size == 0:
                raise ValueError("No brain voxels found in image")
            mu = float(np.mean(vals))
            sigma = float(np.std(vals))
            snr_est = mu / (sigma + 1e-8)
            subject_scores[subj_name] = {
                'score': float(snr_est),
                'file': target_path,
                'snr': float(snr_est)
            }
            print(f"  {subj_name}: Mean SNR = {snr_est:.4f}")
        except Exception as e:
            print(f"Error processing {subj_name}: {e}")
    return subject_scores


def main():
    subjects = collect_subjects()
    if not subjects:
        print("No valid subjects to plot.")
        return

    for subj_name, info in subjects.items():
        # prefer atlas-aligned if available
        candidates = glob.glob(os.path.join(CACHE_DIR, f"{subj_name}*aligned*.nii.gz"))
        if candidates:
            img_path = candidates[0]
        else:
            img_path = info['file']

        print(f"Plotting {subj_name} -> {img_path}")
        fig = plt.figure(figsize=(6, 6))
        ax = fig.add_subplot(111)
        plotting.plot_anat(img_path, axes=ax,
                           title=None,
                           display_mode='ortho', dim=-1, annotate=False, draw_cross=False,
                           colorbar=False)

        # clear titles/texts
        ax.set_title("")
        for txt in list(ax.texts):
            txt.set_visible(False)

        # remove any thin colorbar axes
        for extra_ax in list(fig.axes):
            pos = extra_ax.get_position()
            if pos.width < 0.06 or pos.height < 0.06:
                try:
                    fig.delaxes(extra_ax)
                except Exception:
                    pass

        out_file = f"{subj_name}_recon.png"
        plt.savefig(out_file, dpi=300, bbox_inches='tight')
        plt.close(fig)
        print(f"Saved {out_file}")


if __name__ == '__main__':
    main()
