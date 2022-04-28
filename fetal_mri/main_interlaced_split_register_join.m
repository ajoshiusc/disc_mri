clear all;close all;clc;
addpath(genpath('/home/ajoshi/projects/svreg/src'));
addpath(genpath('/home/ajoshi/projects/svreg/3rdParty'));
addpath(genpath('/home/ajoshi/projects/svreg/MEX_Files'));

v1=load_untouch_nii('/home/ajoshi/Downloads/disc_data/fetal_mri/fetal_vol2_t2_haste_trufi/t2_haste_cor_TE119/_t2_haste_cor_TE119_20210915181625_9.nii');

v1_1 = make_nii((v1.img(:,:,1:2:end)),[1.5,1.5,6]);
save_nii(v1_1,'tmp1.nii.gz');
v1_2 = make_nii((v1.img(:,:,2:2:end)),[1.5,1.5,6]);
save_nii(v1_2,'tmp2.nii.gz');

tic
unix('fnirt --ref=tmp1.nii.gz --in=tmp2.nii.gz --iout=warpedimg.nii.gz --warpres=10,10,40 --fout=warpingfield.nii.gz --applyinmask=0 --applyrefmask=0 --estint=1 --reffwhm=50 --infwhm=50 --miter=5 --subsamp=4 --lambda=300' );
toc

v1_2 = load_nii('warpedimg.nii.gz');

v1.img(:,:,2:2:end)=v1_2.img;

save_untouch_nii_gz(v1,'merged.nii.gz');