# ||AUM||
# Shree Ganeshaya Namaha

import scipy.io
import scipy as sp
import numpy as np
from fmri_methods_sipi import rot_sub_data
from surfproc import view_patch_vtk, view_patch, patch_color_attrib
from dfsio import readdfs
import os
import itertools
from random import randint

p_dir = '/data_disk/HCP_data/data'
p_dir_ref = '/data_disk/HCP_data'
lst = os.listdir(p_dir)

r_factor = 3
ref_dir = os.path.join(p_dir_ref, 'reference.old')
nClusters = 30

ref = '100307'
print(ref + '.reduce' + str(r_factor) + '.LR_mask.mat')
fn1 = ref + '.reduce' + str(r_factor) + '.LR_mask.mat'
fname1 = os.path.join(ref_dir, fn1)
msk = scipy.io.loadmat(fname1)  # h5py.File(fname1);
dfs_left = readdfs(os.path.join(p_dir_ref, 'reference.old', ref + '.aparc.\
a2009s.32k_fs.reduce3.left.dfs'))
dfs_left_sm = readdfs(os.path.join(p_dir_ref, 'reference.old', ref + '.aparc.\
a2009s.32k_fs.reduce3.very_smooth.left.dfs'))
view_patch_vtk(dfs_left_sm, azimuth=90, elevation=180, roll=90,
               outfile='sub.png', show=1)

count1 = 0
rho_rho = []
rho_all = []
cc_msk = (dfs_left.labels > 0)

sub = lst[0]
data = scipy.io.loadmat(os.path.join(p_dir, sub, sub + '.rfMRI_REST1_LR.\
reduce3.ftdata.NLM_11N_hvar_25.mat'))
LR_flag = msk['LR_flag']
LR_flag = np.squeeze(LR_flag) != 0
data = data['ftdata_NLM']
temp = data[LR_flag, :]
m = np.mean(temp, 1)
temp = temp - m[:, None]
s = np.std(temp, 1)+1e-116
temp = temp/s[:, None]
d1 = temp  # [cc_msk, :]
win_lengths = np.arange(5, d1.shape[1], 20)
nboot = 20
nbootiter = np.arange(nboot)
step_sizes = [5,6,7,8,9,10]#[1,2,3,4]

cfull = np.dot(d1, d1.T)/d1.shape[1]
cnt = 0
sz = np.arange(2, d1.shape[1], 20)
err = np.zeros((len(win_lengths), nboot, len(step_sizes)))

for nb, iWinL, step in itertools.product(nbootiter, np.arange(len(win_lengths)), step_sizes):
    WinL = win_lengths[iWinL]
    startpt = randint(0, data.shape[1])
    t = np.arange(startpt, startpt + WinL, step)
    t = np.mod(t, data.shape[1])
    temp = data[LR_flag, :]
    temp = temp[:, t]
    m = np.mean(temp, 1)
    temp = temp - m[:, None]
    s = np.std(temp, axis=1)+1e-116
    temp = temp/s[:, None]
    d1 = temp

    c = np.dot(d1, d1.T)/WinL
    err[iWinL, nb, step-5] = sp.linalg.norm(cfull-c)
    print(step, WinL, nb, err[iWinL, nb, step-5])

np.savez_compressed('corr_samples_step5_10.npz', err=err, win_lengths=win_lengths)
