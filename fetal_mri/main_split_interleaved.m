clear all;close all;clc;
addpath(genpath('/home/ajoshi/projects/svreg/src'));
addpath(genpath('/home/ajoshi/projects/svreg/3rdParty'));
addpath(genpath('/home/ajoshi/projects/svreg/MEX_Files'));

infile = '/home/ajoshi/Desktop/fetal_scan/haste/haste_cor.nii.gz';
outfile1 = '/home/ajoshi/Desktop/fetal_scan/haste/haste_cor_1.nii.gz';
outfile2 = '/home/ajoshi/Desktop/fetal_scan/haste/haste_cor_2.nii.gz';

v1=load_untouch_nii(infile);
img = v1.img(:,:,1:2:end);
res = v1.hdr.dime.pixdim(2:4);
v = make_nii(img, [res(1),res(2),2*res(3)], [], v1.hdr.dime.datatype);
save_nii(v, outfile1);

img = v1.img(:,:,2:2:end);
res = v1.hdr.dime.pixdim(2:4);
v = make_nii(img, [res(1),res(2),2*res(3)], [], v1.hdr.dime.datatype);
save_nii(v, outfile2);




