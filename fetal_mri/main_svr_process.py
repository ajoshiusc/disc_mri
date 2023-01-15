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

subdir = '/deneb_disk/fetal_scan_1_9_2023/morning/nii_files_rot'
template = subdir + '/p28_t2_haste_sag_head_p.nii.gz'
mask = subdir + '/p28_t2_haste_sag_head_p_mask.nii.gz'

outsvr = subdir + '/outsvr.nii.gz'

stacks = glob.glob(subdir+'/*head*p.nii.gz')

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

    if os.path.isfile(outsvr_aligned):
        continue

    cmd = 'mirtksvr reconstruct ' + outsvr + ' ' + \
        str(num_stacks) + str_stacks + ' --resolution ' + str(res)

    cmd += ' --thickness' + str_th + ' --template ' + template + ' --mask ' + mask

    print(cmd)
    os.system(cmd)

    cmd = 'flirt -in ' + outsvr + ' -ref /home/ajoshi/projects/disc_mri/fetal_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA31.nii.gz -out ' + \
        outsvr_aligned+' -dof 7 -omat reorient.mat -searchrx -180 180 -searchry -180 180 -searchrz -180 180'

    print(cmd)
    os.system(cmd)


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
    val_ssim[num_stacks-1] = m.forward(x, y)

print(val_ssim)

x = range(1, len(stacks)+1)

plt.xticks(np.arange(min(x), max(x)+1, 1.0))

plt.plot(x[2:], val_ssim[2:])
plt.savefig('ssim.png')


plt.plot(x[2:], val_mse[2:])
plt.savefig('mse.png')
