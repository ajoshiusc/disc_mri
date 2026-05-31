import numpy as np

def print_cv(name, file_npz):
    data = np.load(file_npz)
    roi_vols = data["roi_vols"] 
    if roi_vols.ndim == 4:
        v = roi_vols[:, :, 0, 1:-1]
    else:
        v = roi_vols
    
    v1 = v[0]
    v2 = v[1]
    
    mean_v = (v1 + v2) / 2.0
    # avoid division by zero or very small numbers
    valid = mean_v > 0
    abs_diff = np.abs(v1[valid] - v2[valid])
    
    # % CV is std / mean. For test-retest (2 measurements), std = abs_diff / sqrt(2)
    cv = (abs_diff / np.sqrt(2)) / mean_v[valid]
    
    median_cv = np.nanmedian(cv) * 100
    mean_cv = np.nanmean(cv) * 100
    
    print(f"{name}: Median CV = {median_cv:.2f}%, Mean CV = {mean_cv:.2f}%")

base_dir = "/home/ajoshi/Projects/disc_mri/low_field_high_field_mprage_comparison/"
print_cv("BrainSuite 0.55T", base_dir + "brainSuite_low_field.npz")
print_cv("BrainSuite 3T", base_dir + "brainSuite_3T.npz")
print_cv("FreeSurfer 0.55T", base_dir + "freesurfer_low_field.npz")
print_cv("FreeSurfer 3T", base_dir + "freesurfer_3T.npz")
