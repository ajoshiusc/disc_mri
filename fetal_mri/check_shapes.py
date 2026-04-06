import nibabel as nib
import glob
import os

SUBJECTS = [
    ("subj_8_11_2023", "/deneb_disk/disc_mri/scan_8_11_2023/outsvr", "svr_te140_numstacks_*_aligned.nii.gz", "svr_te140_numstacks_*.nii.gz"),
    ("subj_9_12_2023", "/deneb_disk/disc_mri/scan_9_12_2023/outsvr", "svr_te140_numstacks_*_aligned.nii.gz", "svr_te140_numstacks_*.nii.gz"),
    ("subj_11_3_2023_babya", "/deneb_disk/disc_mri/scan_11_3_2023_twins_nii_rot/outsvr", "svr_te140_babya_numstacks_*.nii.gz", "svr_te140_babya_numstacks_*.nii.gz"),
    ("subj_11_3_2023_babyb", "/deneb_disk/disc_mri/scan_11_3_2023_twins_nii_rot/outsvr", "svr_te140_babyb_numstacks_*.nii.gz", "svr_te140_babyb_numstacks_*.nii.gz"),
    ("subj_3_20_2024", "/deneb_disk/disc_mri/scan_3_20_2024/outsvr", "svr_te140_numstacks_*_aligned.nii.gz", "svr_te140_numstacks_*.nii.gz"),
    ("subj_10_23_2025", "/home/ajoshi/project2_ajoshi_27/data/disc_mri/scan_10_23_2025/outsvr", "svr_te140*numstacks_*.nii.gz", "svr_te140*numstacks_*.nii.gz"),
    ("subj_12_03_2025", "/home/ajoshi/project2_ajoshi_27/data/disc_mri/scan_12_03_2025/outsvr", "svr_te140*numstacks_*.nii.gz", "svr_te140*numstacks_*.nii.gz"),
    ("subj_1_8_2026", "/home/ajoshi/project2_ajoshi_27/data/disc_mri/scan_1_8_2026/outsvr", "svr_te140*numstacks_*.nii.gz", "svr_te140*numstacks_*.nii.gz"),
    ("subj_2_6_2026", "/home/ajoshi/project2_ajoshi_27/data/disc_mri/scan_2_6_2026/outsvr", "svr_te140*numstacks_*.nii.gz", "svr_te140*numstacks_*.nii.gz"),
    ("subj_2_9_2026", "/home/ajoshi/project2_ajoshi_27/data/disc_mri/scan_2_9_2026/outsvr", "svr_te140*numstacks_*.nii.gz", "svr_te140*numstacks_*.nii.gz"),
]

for name, d, pat1, pat2 in SUBJECTS:
    files = glob.glob(os.path.join(d, pat1))
    if not files:
        files = glob.glob(os.path.join(d, pat2))
    if files:
        f = files[0]
        try:
            shp = nib.load(f).shape
            print(f"{name:25s} {len(files):4d} files found. Shape: {shp}")
        except Exception as e:
            print(f"{name:25s} Error reading {f}: {e}")
    else:
        print(f"{name:25s} 0 files found.")
