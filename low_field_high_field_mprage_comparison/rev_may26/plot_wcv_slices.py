import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import nibabel as nib
from nilearn import plotting
import os

def build_wcv_img(npz_file, dict_name='roi_vols'):
    data = np.load(npz_file)
    v = data[dict_name]
    if v.ndim == 4:
         v = v[:, :, 0, 1:-1]
    
    v1 = v[0] 
    v2 = v[1] 
    N = v1.shape[0] 
    var_w = np.sum((v1 - v2)**2, axis=0) / (2 * N)
    m = np.mean((v1 + v2) / 2.0, axis=0)
    wcv = np.zeros_like(m)
    valid = m > 0
    wcv[valid] = np.sqrt(var_w[valid]) / m[valid] * 100
    
    label_ids = data["label_ids"]
    if v.shape[-1] == len(label_ids) - 2:
        label_ids = label_ids[1:-1]
    
    return wcv, label_ids

def create_wcv_nifti(wcv, label_ids, atlas_path):
    atlas_img = nib.load(atlas_path)
    atlas_data = atlas_img.get_fdata()
    
    wcv_map = np.zeros_like(atlas_data)
    for value, label in zip(wcv, label_ids):
        # We put 0 instead of small wCV maybe? No limit is drawn in plot.
        # But we don't want background (0) to get colored. Let's make sure label != 0.
        if label != 0:
            wcv_map[atlas_data == label] = value
    
    # Optional: fill background with np.nan so it is transparent
    # wcv_map[atlas_data == 0] = np.nan
    wcv_nifti = nib.Nifti1Image(wcv_map, atlas_img.affine)
    return wcv_nifti

bs_wcv_lf, bs_labels_lf = build_wcv_img('../brainSuite_low_field.npz')
bs_wcv_3t, bs_labels_3t = build_wcv_img('../brainSuite_3T.npz')

atlas = "/home/ajoshi/Software/BrainSuite23a/svreg/BrainSuiteAtlas1/mri.label.nii.gz"
bg = "/home/ajoshi/Software/BrainSuite23a/svreg/BrainSuiteAtlas1/mri.bfc.nii.gz"

img_lf = create_wcv_nifti(bs_wcv_lf, bs_labels_lf, atlas)
img_3t = create_wcv_nifti(bs_wcv_3t, bs_labels_3t, atlas)

fig, axes = plt.subplots(2, 1, figsize=(10, 8))
plotting.plot_stat_map(img_lf, bg_img=bg, axes=axes[0], title='BrainSuite 0.55T Test-Retest Volume wCV (%)', vmax=12, cmap='hot', draw_cross=False)
plotting.plot_stat_map(img_3t, bg_img=bg, axes=axes[1], title='BrainSuite 3T Test-Retest Volume wCV (%)', vmax=12, cmap='hot', draw_cross=False)

plt.tight_layout()
fig.savefig('supplementary_wcv_volume_slices.pdf')
