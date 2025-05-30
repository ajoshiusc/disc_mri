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
import matplotlib.pyplot as plt
import nibabel as nib


def calculate_white_matter_snr(image_path, wm_mask_path):
    # Load the NIfTI image
    img = nib.load(image_path)
    data = img.get_fdata()

    # Load the white matter mask
    white_matter_mask = nib.load(wm_mask_path).get_fdata() > 0

    # Calculate mean signal intensity in white matter
    white_matter_mean = np.mean(data[white_matter_mask])

    # Calculate standard deviation of background noise
    # Background noise can be estimated from regions outside the brain
    # background_mask = data <= np.mean(data)
    background_std = np.std(data[white_matter_mask])

    # background_std = np.std(data[background_mask])

    # Calculate SNR
    white_matter_snr = white_matter_mean / background_std

    return white_matter_snr


te_all = [98, 140, 181, 272]

for te in te_all:


    MAX_COMB = 20

    subdir = "/deneb_disk/fetal_data_8_11_2023/nifti_data_rot"
    template = subdir + "/p21_t2_haste_tra_head_te98_p.nii.gz"
    mask = subdir + "/p21_t2_haste_tra_head_te98_p.mask.nii.gz"
    fetal_atlas = (
        "/deneb_disk/disc_mri/fetal_atlas//CRL_FetalBrainAtlas_2017v3/STA30.nii.gz"
    )
    fetal_atlas_seg = (
        "/deneb_disk/disc_mri/fetal_atlas//CRL_FetalBrainAtlas_2017v3/STA30_regional.nii.gz"
    )
    fetal_atlas_tissue = (
        "/deneb_disk/disc_mri/fetal_atlas//CRL_FetalBrainAtlas_2017v3/STA30_regional.nii.gz"
    )
    wm_eroded_mask = "/deneb_disk/disc_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA30_wm_eroded_mask.nii.gz"

    outsvr_dir = "/deneb_disk/disc_mri/scan_8_11_2023/outsvr"

    if not os.path.exists(wm_eroded_mask):

        # read tissue mask fetal_atlas_tissue using simpleitk, create mask corresponding to the tissue labels 121 and 120, erode the mask by 3 voxels in 3D and save the mask to a nifti file

        img = sitk.ReadImage(fetal_atlas_tissue)
        data = sitk.GetArrayFromImage(img)
        wmmask = np.zeros(data.shape, dtype=np.uint16)
        wmmask[data == 121] = 1
        wmmask[data == 120] = 1
        wmmask = sitk.GetImageFromArray(wmmask)
        wmmask = sitk.BinaryErode(wmmask, (1, 1, 1), sitk.sitkBall)
        affine = img.GetDirection()
        wmmask.SetDirection(affine)
        wmmask.SetOrigin(img.GetOrigin()[:3])
        wmmask.SetSpacing(img.GetSpacing())

        sitk.WriteImage(wmmask, wm_eroded_mask)


    """
    subdir = "/deneb_disk/fetal_data_8_11_2023/nifti_data_rot"
    template = subdir + "/p10_t2_haste_tra_head_te140_p.nii.gz"
    mask = subdir + '/p10_t2_haste_tra_head_te140_p.mask.nii.gz'
    fetal_atlas = "/deneb_disk/disc_mri/fetal_atlas//CRL_FetalBrainAtlas_2017v3/STA30.nii.gz"
    fetal_atlas_seg = "/deneb_disk/disc_mri/fetal_atlas//CRL_FetalBrainAtlas_2017v3/STA30_regional.nii.gz"
    fetal_atlas_tissue = "/deneb_disk/disc_mri/fetal_atlas//CRL_FetalBrainAtlas_2017v3/STA30_tissue.nii.gz"

    subdir = "/deneb_disk/fetal_data_8_11_2023/nifti_data_rot"
    template = subdir + "/p34_t2_haste_tra_head_te181_p.nii.gz"
    mask = subdir + '/p34_t2_haste_tra_head_te181_p.mask.nii.gz'

    fetal_atlas = "/deneb_disk/disc_mri/fetal_atlas//CRL_FetalBrainAtlas_2017v3/STA30.nii.gz"
    fetal_atlas_seg = "/deneb_disk/disc_mri/fetal_atlas//CRL_FetalBrainAtlas_2017v3/STA30_regional.nii.gz"
    fetal_atlas_tissue = "/deneb_disk/disc_mri/fetal_atlas//CRL_FetalBrainAtlas_2017v3/STA30_tissue.nii.gz"
    """

    stacks = glob.glob(subdir + f"/*head*te{te}*p.nii.gz")

    res = 1
    th = 3


    num_stacks = len(stacks)

    outsvr = f"{outsvr_dir}/svr_te{te}_numstacks_{num_stacks}_iter_{0}_masked.nii.gz"
    outsvr_aligned = f"{outsvr_dir}/svr_te{te}_aligned.nii.gz"

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
        outsvr = f"{outsvr_dir}/svr_te{te}_numstacks_{num_stacks}_iter_{ns}.nii.gz"
        outsvr_aligned = (
            f"{outsvr_dir}/svr_te{te}_numstacks_{num_stacks}_iter_{ns}_aligned.nii.gz"
        )

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

        print(cmd)
        os.system(cmd)


    val_ssim = np.zeros((len(stacks), MAX_COMB))
    val_mse = np.zeros((len(stacks), MAX_COMB))
    wm_snr = np.zeros((len(stacks), MAX_COMB))


    mse = MSELoss()
    ssim = SSIMLoss(spatial_dims=3)

    for ns, i in product(range(len(stacks)), range(MAX_COMB)):
        outsvr_aligned = f"{outsvr_dir}/svr_te{te}_numstacks_{ns+1}_iter_{i}_aligned.nii.gz"
        target = f"{outsvr_dir}/svr_te{te}_aligned.nii.gz"

        x = load_img(outsvr_aligned).get_fdata()
        y = load_img(target).get_fdata()
        x *= y > 0

        """# plot x and y images
        plt.imshow(x[100, :, :])
        plt.savefig(f"image_x_{ns}_{i}.png")
        plt.close()

        plt.imshow(y[100, :, :])
        plt.savefig(f"image_y_{ns}_{i}.png")
        plt.close()"""

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
        wm_snr[ns, i] = calculate_white_matter_snr(outsvr_aligned, wm_eroded_mask)

    print(val_ssim, val_mse)

    np.savez(
        f"ssim_mse_wm_snr_3_17_2025_{te}_mask.npz",
        val_ssim=val_ssim,
        val_mse=val_mse,
        wm_snr=wm_snr,
    )

    x = range(1, len(stacks) + 1)

    plt.xticks(np.arange(min(x), max(x) + 1, 1.0))

    plt.plot(x[2:], val_ssim[2:])
    plt.savefig(f"ssim_{te}.png")

    plt.close()

    plt.xticks(np.arange(min(x), max(x) + 1, 1.0))

    plt.plot(x[2:], val_mse[2:])
    plt.savefig(f"mse_{te}.png")

    plt.xticks(np.arange(min(x), max(x) + 1, 1.0))

    plt.plot(x[2:], wm_snr[2:])
    plt.savefig("wm_snr.png")

    plt.close()

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
