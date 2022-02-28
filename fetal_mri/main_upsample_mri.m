clear all;close all;clc;
addpath(genpath('/home/ajoshi/projects/svreg/src'));
addpath(genpath('/home/ajoshi/projects/svreg/3rdParty'));
addpath(genpath('/home/ajoshi/projects/svreg/MEX_Files'));

v1=load_untouch_nii('out2_2.nii.gz');

v1.img = double(v1.img);
vout=v1;

size_x = size(v1.img,2);
size_y = size(v1.img,3);


vout.hdr.dime.pixdim(2)=vout.hdr.dime.pixdim(2)/2.0;
vout.hdr.dime.dim(2)=2*size(v1.img,1);
vout.img=zeros(size(v1.img,1)*2,size(v1.img,2),size(v1.img,3));
vout.img(2:2:end,:,:)=v1.img;
save_untouch_nii_gz(vout,'temp.nii.gz');
[X,Y]=meshgrid(1:size_x,1:size_y);
v1_rescaled=255*(v1.img/max(v1.img(:)));

for j = 1:size(v1.img,1)-1

    I1 = v1_rescaled(j,:,:); I1=permute(I1,[2,3,1]);
    I2 = squeeze(v1_rescaled(j+1,:,:));

    I1 = imresize(I1,[256,256]);
    I2 = imresize(I2,[256,256]);
    [~,~,~,Tx1,Ty1] = demon_image_registration_mri(I1,I2);
    [~,~,~,Tx2,Ty2] = demon_image_registration_mri(I2,I1);

    Tx1 = (size_x/256) * imresize(Tx1,[size_x,size_y]);
    Tx2 = (size_x/256) * imresize(Tx2,[size_x,size_y]);
    Ty1 = (size_x/256) * imresize(Ty1,[size_x,size_y]);
    Ty2 = (size_x/256) * imresize(Ty2,[size_x,size_y]);
    
    IW1=interp2(squeeze(v1.img(j+1,:,:)),X+Tx1/2,Y+Ty1/2,'cubic');
    IW2=interp2(squeeze(v1.img(j,:,:)),X+Tx2/2,Y+Ty2/2,'cubic');
    
    vout.img(2*j+1,:,:)=imresize((IW1+IW2)/2,size(v1.img,2:3));
j
end

save_untouch_nii_gz(vout,'out2_up.nii.gz');


