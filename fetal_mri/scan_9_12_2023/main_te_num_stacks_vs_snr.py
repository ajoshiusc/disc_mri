import nilearn.image as ni
from sklearn.feature_extraction import img_to_graph
import numpy as np
import os
import SimpleITK as sitk
import glob
from monai.metrics.regression import SSIMMetric, MSEMetric
from nilearn.image import load_img
from monai.transforms import EnsureChannelFirst
from tqdm import tqdm
from monai.losses.ssim_loss import SSIMLoss
from torch.nn import MSELoss

# from itertools import product
from tqdm.contrib.itertools import product

import matplotlib.pyplot as plt


te = 140
MAX_COMB = 20

subdir = "/deneb_disk/fetal_scan_9_12_2023/vol0700_nii_rot"
template = subdir + "/p22_t2_haste_tra_head_te98_p.nii.gz"
mask = subdir + '/p22_t2_haste_tra_head_te98_p.mask.nii.gz'
fetal_atlas = "/deneb_disk/disc_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA37exp.nii.gz"
fetal_atlas_seg = "/deneb_disk/disc_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA37exp_regional.nii.gz"
fetal_atlas_tissue = "/deneb_disk/disc_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA37exp_tissue.nii.gz"
wm_eroded_mask = "/deneb_disk/disc_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA37exp_wm_eroded_mask.nii.gz"


if not os.path.exists(wm_eroded_mask):

    #read tissue mask fetal_atlas_tissue using simpleitk, create mask corresponding to the tissue labels 121 and 120, erode the mask by 3 voxels in 3D and save the mask to a nifti file

    img=sitk.ReadImage(fetal_atlas_tissue)
    data = sitk.GetArrayFromImage(img)
    mask = np.zeros(data.shape, dtype=np.uint16)
    mask[data == 121] = 1
    mask[data == 120] = 1
    mask = sitk.GetImageFromArray(mask)
    mask = sitk.BinaryErode(mask, (3,3,3), sitk.sitkBall)
    affine = img.GetDirection()
    mask.SetDirection(affine)
    mask.SetOrigin(img.GetOrigin()[:3])
    mask.SetSpacing(img.GetSpacing())

    sitk.WriteImage(mask, wm_eroded_mask)




stacks = glob.glob(subdir + f"/*head*te{te}*p.nii.gz")

res = 1
th = 3


num_stacks = len(stacks)

outsvr = f"/deneb_disk/disc_mri/scan_9_12_2023/outsvr/svr_te{te}_numstacks_{num_stacks}_iter_{0}_masked.nii.gz"
outsvr_aligned = f"/deneb_disk/disc_mri/scan_9_12_2023/outsvr/svr_te{te}_aligned.nii.gz"

if not os.path.exists(outsvr_aligned):

    cmd = (
        "flirt -in "
        + outsvr
        + " -ref "
        + fetal_atlas
        + " -out "
        + outsvr_aligned
        + " -dof 6 -omat "
        + f"reorient_te{te}.mat"
        + " -searchrx -180 180 -searchry -180 180 -searchrz -180 180 -cost mutualinfo"
    )

    print(cmd)
    os.system(cmd)

print("registration of svr to atlas done")


for num_stacks, ns in product(range(1, len(stacks) + 1), range(MAX_COMB)):
    outsvr = f"/deneb_disk/disc_mri/scan_9_12_2023/outsvr/svr_te{te}_numstacks_{num_stacks}_iter_{ns}.nii.gz"
    outsvr_aligned = f"/deneb_disk/disc_mri/scan_9_12_2023/outsvr/svr_te{te}_numstacks_{num_stacks}_iter_{ns}_aligned.nii.gz"

    if os.path.exists(outsvr_aligned):
        continue

    cmd = (
        "flirt -in "
        + outsvr
        + " -ref "
        + fetal_atlas
        + " -out "
        + outsvr_aligned
        + " -applyxfm -init "
        + f"reorient_te{te}.mat"
    )

    # print(cmd)
    os.system(cmd)


val_ssim = np.zeros((len(stacks), MAX_COMB))
val_mse = np.zeros((len(stacks), MAX_COMB))
mse = MSELoss()
#ssim = SSIMLoss(spatial_dims=3)

for ns, i in product(range(len(stacks)), range(MAX_COMB)):
    outsvr_aligned = f"/deneb_disk/disc_mri/scan_9_12_2023/outsvr/svr_te{te}_numstacks_{ns+1}_iter_{i}_aligned.nii.gz"
    target = f"/deneb_disk/disc_mri/scan_9_12_2023/outsvr/svr_te{te}_aligned.nii.gz"

    x = load_img(outsvr_aligned).get_fdata()
    y = load_img(target).get_fdata()

    x = EnsureChannelFirst(channel_dim=1)(
        x[
            None,
            None,
        ]
    )
    y = EnsureChannelFirst(channel_dim=1)(
        y[
            None,
            None,
        ]
    )

    data_range = y.max().unsqueeze(0)
    ssim = SSIMLoss(spatial_dims=3, data_range=data_range)
    val_ssim[ns, i] = ssim.forward(x, y)
    val_mse[ns, i] = mse.forward(x, y)

print(val_ssim, val_mse)

np.savez("ssim_mse.npz", val_ssim=val_ssim, val_mse=val_mse)

x = range(1, len(stacks) + 1)

plt.xticks(np.arange(min(x), max(x) + 1, 1.0))

plt.plot(x[2:], val_ssim[2:])
plt.savefig("ssim.png")

plt.close()

plt.xticks(np.arange(min(x), max(x) + 1, 1.0))

plt.plot(x[2:], val_mse[2:])
plt.savefig("mse.png")


"""
# warp atlas to subject

for num_stacks in tqdm(range(1, len(stacks)+1)):

    outsvr_aligned = subdir + '/outsvr'+'_'+str(num_stacks)+'_aligned.nii.gz'
    atlas_reg = subdir + '/outsvr'+'_'+str(num_stacks)+'_atlas_reg.nii.gz'
    atlas_reg_labels = subdir + '/outsvr'+'_'+str(num_stacks)+'_atlas_reg_labels.nii.gz'
    atlas_reg_tissue = subdir + '/outsvr'+'_'+str(num_stacks)+'_atlas_reg_tissue.nii.gz'
    warped_atlas_reg = subdir + '/outsvr'+'_'+str(num_stacks)+'_warped_atlas_reg.nii.gz'
    warped_tissue_reg = subdir + '/outsvr'+'_'+str(num_stacks)+'_warped_tissue_reg.nii.gz'
    warped_labels_reg = subdir + '/outsvr'+'_'+str(num_stacks)+'_warped_labels_reg.nii.gz'

    cmd = 'flirt -ref ' + outsvr_aligned + ' -in ' + fetal_atlas  + ' -out ' + atlas_reg + ' -omat reg.mat'
    os.system(cmd)

    cmd = 'flirt -ref ' + outsvr_aligned + ' -in ' + fetal_atlas_seg + ' -out ' + atlas_reg_labels + ' -init reg.mat -applyxfm -interp nearestneighbour'
    os.system(cmd)

    cmd = 'flirt -ref ' + outsvr_aligned + ' -in ' + fetal_atlas_tissue + ' -out ' + atlas_reg_tissue + ' -init reg.mat -applyxfm -interp nearestneighbour'
    os.system(cmd)


    cmd = 'fnirt --ref=' + outsvr_aligned +' --in=' + fetal_atlas + ' --aff=reg.mat --cout=fnirtcoeff.nii.gz'
    os.system(cmd)

    cmd = 'applywarp -r ' + outsvr_aligned + ' -i ' + fetal_atlas + ' -o ' + warped_atlas_reg + ' -w fnirtcoeff.nii.gz' 
    os.system(cmd)

    cmd = 'applywarp -r  ' + outsvr_aligned + ' -i ' + fetal_atlas_tissue + ' -o ' + warped_tissue_reg +' -w fnirtcoeff.nii.gz --interp=nn'
    os.system(cmd)

    cmd = 'applywarp -r '+ outsvr_aligned + ' -i ' + fetal_atlas_seg + ' -o ' + warped_labels_reg + ' -w fnirtcoeff.nii.gz --interp=nn'
    os.system(cmd)

"""
