# ||AUM||
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
win_lengths = sp.arange(5, d1.shape[1], 20)
nboot = 200
nbootiter = sp.arange(nboot)

cfull = sp.dot(d1, d1.T)/d1.shape[1]
cnt = 0
sz = sp.arange(2, d1.shape[1], 20)
err = sp.zeros((len(win_lengths), nboot))

for nb, iWinL in itertools.product(nbootiter, sp.arange(len(win_lengths))):
    WinL = win_lengths[iWinL]
    startpt = randint(0, data.shape[1])
    t = sp.arange(startpt, startpt + WinL)
    t = sp.mod(t, data.shape[1])
    temp = data[LR_flag, :]
    temp = temp[:, t]
    m = np.mean(temp, 1)
    temp = temp - m[:, None]
    s = sp.std(temp, axis=1)+1e-116
    temp = temp/s[:, None]
    d1 = temp

    c = sp.dot(d1, d1.T)/WinL
    err[iWinL, nb] = sp.linalg.norm(cfull-c)
    print(WinL, nb, err[iWinL, nb])

sp.savez_compressed('corr_samples.npz', err=err, win_lengths=win_lengths)
