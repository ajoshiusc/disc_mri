
import nilearn.image as ni
import os
from nilearn.plotting import plot_stat_map
from glob import glob
from brainsync import normalizeData, brainSync
import scipy.io as spio
import numpy as np
from numpy.linalg import norm
from grayord_utils import visdata_grayord

anat = '/deneb_disk/PNS_fMRI/PNS_fMRI/PNS_FMRI_20230215/bfpout/vol561/anat/vol561_T1w.bfc.nii.gz'

fmri_off = '/deneb_disk/PNS_fMRI/PNS_fMRI/PNS_FMRI_20230215/bfpout/vol561/func/vol561_11_ep2d_bold_4mm_tr3000_6min_pns_off_baseline_bold.32k.GOrd.mat'
fmri_on = '/deneb_disk/PNS_fMRI/PNS_fMRI/PNS_FMRI_20230215/bfpout/vol561/func/vol561_3_ep2d_bold_4mm_tr3000_6min_pns_on_bold.32k.GOrd.mat'


foff = spio.loadmat(fmri_off)['dtseries'].T
fon = spio.loadmat(fmri_on)['dtseries'].T

foff, _, _ = normalizeData(foff)
fon, _, _ = normalizeData(fon)


foff_sync, _ = brainSync(fon,foff)


diff_before = norm(fon - foff, axis=0)
diff_after = norm(fon - foff_sync, axis=0)

diff = diff_before - diff_after

visdata_grayord(diff, surf_name='pns_on_off_right', out_dir='.', smooth_iter=10, colorbar_lim=[0,.6], colormap='jet', save_png=True, bfp_path='/home/ajoshi/projects/bfp', fsl_path='/home/ajoshi/webware/fsl')


