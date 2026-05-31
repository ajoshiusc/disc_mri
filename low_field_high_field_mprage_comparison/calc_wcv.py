import numpy as np

def print_wcv(name, file_npz):
    data = np.load(file_npz)
    roi_vols = data["roi_vols"] 
    if roi_vols.ndim == 4:
        v = roi_vols[:, :, 0, 1:-1]
    else:
        v = roi_vols
    
    v1 = v[0] # Session 1: shape (5 subjects, n_roi)
    v2 = v[1] # Session 2: shape (5 subjects, n_roi)
    
    N = v1.shape[0] # Number of subjects (5)
    
    # Within-subject variance for each ROI
    var_w = np.sum((v1 - v2)**2, axis=0) / (2 * N)
    
    # Grand mean volume for each ROI across all subjects and sessions
    mean_roi = np.mean((v1 + v2) / 2.0, axis=0)
    
    valid = mean_roi > 0
    
    wCV = np.sqrt(var_w[valid]) / mean_roi[valid]
    
    median_wCV = np.nanmedian(wCV) * 100
    mean_wCV = np.nanmean(wCV) * 100
    
    print(f"{name}: Median ROI wCV = {median_wCV:.2f}%, Mean ROI wCV = {mean_wCV:.2f}%")

base_dir = "/home/ajoshi/Projects/disc_mri/low_field_high_field_mprage_comparison/"
print_wcv("BrainSuite 0.55T", base_dir + "brainSuite_low_field.npz")
print_wcv("BrainSuite 3T", base_dir + "brainSuite_3T.npz")
print_wcv("FreeSurfer 0.55T", base_dir + "freesurfer_low_field.npz")
print_wcv("FreeSurfer 3T", base_dir + "freesurfer_3T.npz")
