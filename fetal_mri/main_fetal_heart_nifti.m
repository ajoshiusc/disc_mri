%||AUM||
%||Shree Ganeshaya Namaha||


clear all;close all;clc;
addpath(genpath('/home/ajoshi/projects/svreg/src'));
addpath(genpath('/home/ajoshi/projects/svreg/3rdParty'));
addpath(genpath('/home/ajoshi/projects/svreg/MEX_Files'));

a = load('/deneb_disk/fetal_heart_data_svr_ye_tian_9_5_2022/usc_disc_yt_2022_07_08_142202_multi_slice_golden_angle_spiral_ssfp_slice_30_fov_240_n63_tread3.mat');
a1=a;
res = [1.5,1.5,2];
vol = a.image_recon;

v = make_nii(vol,res);

[R, T] = get_rot_quaternion(a.para.kspace_info);
M=zeros(3,4);
M(1:3,1:3)=R;
T = R*ones(3,1) + T;
M(1:3,4)=T;

v.hdr.hist.qform_code=0;
v.hdr.hist.sform_code=1;
v.hdr.hist.srow_x=M(1,:);
v.hdr.hist.srow_y=M(2,:);
v.hdr.hist.srow_z=M(3,:);

save_nii(v,'heart_1.nii.gz');



a = load('/deneb_disk/fetal_heart_data_svr_ye_tian_9_5_2022/usc_disc_yt_2022_07_08_142038_multi_slice_golden_angle_spiral_ssfp_slice_20_fov_240_n63_tread3.mat');
a2=a;

res = [1.5,1.5,2];
vol = a.image_recon;
v = make_nii(vol,res);
[R, T] = get_rot_quaternion(a.para.kspace_info);
M=zeros(3,4);
M(1:3,1:3)=R;
T = R*ones(3,1) + T;
M(1:3,4)=T;

v.hdr.hist.qform_code=0;
v.hdr.hist.sform_code=1;
v.hdr.hist.srow_x=M(1,:);
v.hdr.hist.srow_y=M(2,:);
v.hdr.hist.srow_z=M(3,:);

save_nii(v,'heart_2.nii.gz');


a = load('/deneb_disk/fetal_heart_data_svr_ye_tian_9_5_2022/usc_disc_yt_2022_07_08_142402_multi_slice_golden_angle_spiral_ssfp_slice_30_fov_240_n63_tread3.mat');
a3=a;

res = [1.5,1.5,2];
vol = a.image_recon;
v = make_nii(vol,res);
[R, T] = get_rot_quaternion(a.para.kspace_info);
M=zeros(3,4);
M(1:3,1:3)=R;
T = R*ones(3,1) + T;
M(1:3,4)=T;

v.hdr.hist.qform_code=0;
v.hdr.hist.sform_code=1;
v.hdr.hist.srow_x=M(1,:);
v.hdr.hist.srow_y=M(2,:);
v.hdr.hist.srow_z=M(3,:);

save_nii(v,'heart_3.nii.gz');




