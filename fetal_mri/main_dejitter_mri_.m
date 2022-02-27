clear all;close all;clc;
addpath(genpath('/home/ajoshi/projects/svreg/src'));
addpath(genpath('/home/ajoshi/projects/svreg/3rdParty'));
addpath(genpath('/home/ajoshi/projects/svreg/MEX_Files'));

v1=load_untouch_nii('/home/ajoshi/Desktop/tmp/haste.nii.gz');

v1.img = double(v1.img);
vout=v1;


for dejitter=1:10
    v1 = vout;
    v1_rescaled=255*(v1.img/max(v1.img(:)));

    for j = 2:size(v1.img,1)-1

        I1 = v1_rescaled([j-1,j+1],:,:); I1=permute(I1,[2,3,1]);
        I2 = squeeze(v1_rescaled(j,:,:));


        tic;
        [Iw,Tx,Ty] = demon_image_registration_mri(I1,repmat(I2,[1,1,2]));
        toc;

        IW=interp2(squeeze(v1.img(j,:,:)),Tx,Ty,'cubic');
        vout.img(j,:,:)=imresize(IW,size(v1.img,2:3));


        fprintf('=====================%d/%d==%d/%d======================',j,size(v1.img,1),dejitter,10);
        close all;
    end

    save_untouch_nii_gz(vout,sprintf('out_%d.nii.gz',dejitter));

end

