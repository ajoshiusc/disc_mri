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

import matplotlib.pyplot as plt

subdir = '/deneb_disk/chla_data_2_21_2023/svr_output/SVR010'
template = subdir + '/pBRAIN_SAG_SSh_TSE_esp56_1201_BRAIN_SAG_SSh_TSE_esp5.6_20220531061652_1201.nii.gz'
mask = subdir + '/pBRAIN_SAG_SSh_TSE_esp56_1201_BRAIN_SAG_SSh_TSE_esp5.6_20220531061652_1201.mask.nii.gz'
fetal_atlas = '/home/ajoshi/projects/disc_mri/fetal_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA25.nii.gz'
fetal_atlas_seg = '/home/ajoshi/projects/disc_mri/fetal_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA25_regional.nii.gz'
fetal_atlas_tissue = '/home/ajoshi/projects/disc_mri/fetal_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA25_tissue.nii.gz'

outsvr = subdir + '/outsvr.nii.gz'

stacks = glob.glob(subdir+'/p*1.nii.gz')

res = 1
th = 3


for num_stacks in range(1, len(stacks)+1):

    str_stacks = ''
    str_th = ''

    for s in stacks[:num_stacks]:
        str_stacks += ' ' + s
        str_th += ' ' + str(th)

    outsvr = subdir + '/outsvr'+'_'+str(num_stacks)+'.nii.gz'
    outsvr_aligned = subdir + '/outsvr'+'_'+str(num_stacks)+'_aligned.nii.gz'

    if not os.path.isfile(outsvr):

        cmd = 'mirtksvr reconstruct ' + outsvr + ' ' + \
            str(num_stacks) + str_stacks + ' --resolution ' + str(res)

        cmd += ' --thickness' + str_th + ' --template ' + template + ' --mask ' + mask

        print(cmd)
        os.system(cmd)

    if not os.path.isfile(outsvr_aligned):

        cmd = 'flirt -in ' + outsvr + ' -ref '+ fetal_atlas +' -out ' + \
            outsvr_aligned+' -dof 6 -omat reorient.mat -searchrx -180 180 -searchry -180 180 -searchrz -180 180'

        print(cmd)
        os.system(cmd)

'''
val_ssim = np.zeros(len(stacks))
val_mse = np.zeros(len(stacks))

for num_stacks in tqdm(range(1, len(stacks)+1)):

    outsvr_aligned = subdir + '/outsvr'+'_'+str(num_stacks)+'_aligned.nii.gz'
    target = subdir + '/outsvr'+'_'+str(len(stacks))+'_aligned.nii.gz'

    x = load_img(outsvr_aligned).get_fdata()
    y = load_img(target).get_fdata()

    x = EnsureChannelFirst(channel_dim=1)(x[None, None, ])
    y = EnsureChannelFirst(channel_dim=1)(y[None, None, ])

    data_range = y.max().unsqueeze(0)
    m = SSIMLoss(spatial_dims=3)
    val_ssim[num_stacks-1] = m.forward(x, y, data_range=data_range)
    m = MSELoss()
    val_mse[num_stacks-1] = m.forward(x, y)

print(val_ssim, val_mse)

x = range(1, len(stacks)+1)

plt.xticks(np.arange(min(x), max(x)+1, 1.0))

plt.plot(x[2:], val_ssim[2:])
plt.savefig('ssim.png')

plt.close()

plt.xticks(np.arange(min(x), max(x)+1, 1.0))

plt.plot(x[2:], val_mse[2:])
plt.savefig('mse.png')


'''

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

  