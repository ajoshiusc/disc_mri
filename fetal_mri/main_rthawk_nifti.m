%||AUM||
%||Shree Ganeshaya Namaha||

clear all;close all;clc;
addpath(genpath('/home/ajoshi/projects/svreg/src'));
addpath(genpath('/home/ajoshi/projects/svreg/3rdParty'));
addpath(genpath('/home/ajoshi/projects/svreg/MEX_Files'));


numstacks=50;
numslices = 60;


vol = zeros(484,484,numslices);
res=[1.1558,1.1558,1];

for n=1:numstacks
    for s=1:numslices
        a = load(sprintf('/home/ajoshi/Downloads/fetal_scan_may_2022/recon_data_rthawk/usc_disc_yt_2022_05_04_145602_multi_slice_golden_angle_spiral_ssfp_slice_60_fov_240_n50_tread3_slice_%02d_stcr.mat',s));
        vol(:,:,s) = a.image_recon(:,:,n);
    end

    v = make_nii(vol,res);

    save_nii(v,sprintf('145602_stack%d.nii.gz',n));

end








