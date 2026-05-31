import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def do_fractional_ba_test_retest(ax, file_npz, title):
    data = np.load(file_npz)
    v = data["roi_vols"]
    if v.ndim == 4:
         v = v[:, :, 0, 1:-1]
    
    # shape: 2 sessions, 5 subjects, N rois
    v1 = np.ravel(v[0])
    v2 = np.ravel(v[1])
    
    m = (v1 + v2) / 2.0
    diff = (v1 - v2)
    valid = m > 0
    m = m[valid]
    diff = diff[valid]
    
    frac_diff = diff / m
    
    ax.scatter(m, frac_diff, alpha=0.5, s=5)
    ax.set_xscale('log')
    ax.axhline(0, color='red', linestyle='--')
    ax.axhline(np.mean(frac_diff) + 1.96*np.std(frac_diff), color='black', linestyle=':')
    ax.axhline(np.mean(frac_diff) - 1.96*np.std(frac_diff), color='black', linestyle=':')
    ax.set_title(title)
    ax.set_xlabel('Mean Volume (mm^3)')
    ax.set_ylabel('Fractional Difference')

fig, axs = plt.subplots(2, 2, figsize=(10, 8))
do_fractional_ba_test_retest(axs[0, 0], '../brainSuite_low_field.npz', 'BrainSuite 0.55T Test-Retest')
do_fractional_ba_test_retest(axs[0, 1], '../brainSuite_3T.npz', 'BrainSuite 3T Test-Retest')
do_fractional_ba_test_retest(axs[1, 0], '../freesurfer_low_field.npz', 'FreeSurfer 0.55T Test-Retest')
do_fractional_ba_test_retest(axs[1, 1], '../freesurfer_3T.npz', 'FreeSurfer 3T Test-Retest')

plt.tight_layout()
fig.savefig('supplementary_fractional_BA_test_retest.pdf')
