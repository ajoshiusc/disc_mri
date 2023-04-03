import nilearn.image as ni
import numpy as np
from scipy.ndimage import binary_fill_holes
import seaborn as sns
import matplotlib.pyplot as plt
from numpy import std, mean, sqrt

img_file1 = '/deneb_disk/fetal_scan_8_3_2022/haste_head_te'+te+'_rot/outsvr_reorient_bst.nii.gz'
tissue_file1 = '/deneb_disk/fetal_scan_8_3_2022/haste_head_te'+te+'_rot/warped_tissue.nii.gz'
wm_tissue_file1 = '/deneb_disk/fetal_scan_8_3_2022/haste_head_te'+te+'_rot/warped_labels.nii.gz'



#correct if the population S.D. is expected to be equal for the two groups.
def cohen_d(x,y):
    nx = len(x)
    ny = len(y)
    dof = nx + ny - 2
    return (mean(x) - mean(y)) / sqrt(((nx-1)*std(x, ddof=1) ** 2 + (ny-1)*std(y, ddof=1) ** 2) / dof)


img1 = ni.load_img(img_file1).get_fdata()
# Convert to int16
lab1 = ni.load_img(tissue_file1).get_fdata()
lab1_wm = ni.load_img(wm_tissue_file1).get_fdata()

gm_ind = (lab1==112) | (lab1 ==113)
gm_val = img1[gm_ind]

wm_ind = (lab1_wm==120) | (lab1_wm ==121)
wm_val = img1[wm_ind]


print(lab1.shape)
print(gm_val.shape)
print(gm_ind)

#plt.hist([gm_val,wm_val],color=['r','b'], bins=30,alpha=.5)
sns.histplot(data=[gm_val,wm_val],color=['r','b'], bins=30,alpha=.5)
plt.legend(labels=["GM intensity","WM intensity"])

#sns.histplot(data=wm_val, bins=30)

plt.show()

d = cohen_d(wm_val,gm_val)

print(d)