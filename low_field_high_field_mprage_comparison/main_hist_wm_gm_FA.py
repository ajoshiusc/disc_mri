import nilearn.image as ni
import numpy as np
from scipy.ndimage import binary_fill_holes
import seaborn as sns
import matplotlib.pyplot as plt
from numpy import std, mean, sqrt
import glob
import os
import SimpleITK as sitk
import uuid

tissue_file = "/deneb_disk/for_haoting/FA_low_to_high/T1_processing/V2_3T_mprage_vol1_GNL.pvc.frac.nii.gz"


# correct if the population S.D. is expected to be equal for the two groups.
def cohen_d(x, y):
    nx = len(x)
    ny = len(y)
    dof = nx + ny - 2
    return (mean(x) - mean(y)) / sqrt(
        ((nx - 1) * std(x, ddof=1) ** 2 + (ny - 1) * std(y, ddof=1) ** 2) / dof
    )


low_field_FA_file = "/deneb_disk/for_haoting/FA_low_to_high/V2_055T_SENSE_vol1_FA_GNL_noz_aligned_affine.nii.gz"
low_field_SER_FA_file = "/deneb_disk/for_haoting/FA_low_to_high/V2_055T_SER_vol1_FA_GNL_noz_aligned_affine.nii.gz"
high_field_FA_file = (
    "/deneb_disk/for_haoting/FA_low_to_high/V2_3T_SENSE_vol1_FA_GNL_noz.nii.gz"
)

FA_file = low_field_SER_FA_file

img = ni.load_img(FA_file).get_fdata()

lab = ni.load_img(tissue_file).get_fdata()

gm_ind = (lab > 1.6) & (lab < 2.4)
gm_val = img[gm_ind]

wm_ind = lab > 2.6
wm_val = img[wm_ind]

wm_msk = np.zeros(img.shape)
wm_msk[wm_ind] = 255
wm_msk = ni.new_img_like(tissue_file, wm_msk)
wm_msk.to_filename("wm_msk.nii.gz")


gm_msk = np.zeros(img.shape)
gm_msk[gm_ind] = 255
gm_msk = ni.new_img_like(tissue_file, gm_msk)
gm_msk.to_filename("gm_msk.nii.gz")


print(lab.shape)
print(gm_val.shape)
print(gm_ind)

# plt.hist([gm_val,wm_val],color=['r','b'], bins=30,alpha=.5)
s = sns.histplot(data=[gm_val, wm_val], color=["r", "b"], bins=30, alpha=0.5)
plt.legend(labels=["GM image intensity", "WM image intensity"])

# sns.histplot(data=wm_val, bins=30)


d = cohen_d(wm_val, gm_val)
gmstd = np.std(gm_val)
wmstd = np.std(wm_val)

s.set(
    title=f"low_field_ser, "
    + f"Cohens d: {d:.2f}, GM std: {gmstd:.2f}, WM std: {wmstd:.2f}"
)
# plt.show()

s.figure.savefig(f"low_field_ser.png")

plt.close()

print(f"Cohens d: {d}, GM std: {gmstd}, WM std: {wmstd}")
