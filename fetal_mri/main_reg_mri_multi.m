clear all;close all;clc;
addpath(genpath('/home/ajoshi/projects/svreg/src'));
addpath(genpath('/home/ajoshi/projects/svreg/3rdParty'));
addpath(genpath('/home/ajoshi/projects/svreg/MEX_Files'));

v=load_untouch_nii('/home/ajoshi/Desktop/tmp/haste.nii.gz');

v.img = double(v.img);
v.img=255*(v.img/max(v.img(:)));

I1 = imresize(squeeze(v.img(1,:,:)),[256,256]);
I2 = imresize(squeeze(v.img(2,:,:)),[256,256]);


tic;
[Iw,Tx,Ty] = demon_image_registration_mri(repmat(I1,[1,1,2]),repmat(I2,[1,1,2]));
toc;

IC=checkerboard(4,32,32);IC=255*double(IC);
ICW=interp2(IC,Tx,Ty,'cubic');


figure;
imagesc(255*IC);colormap gray;

figure;
imagesc(255*ICW);colormap gray;
