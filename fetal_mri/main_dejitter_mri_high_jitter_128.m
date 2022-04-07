clear all;close all;clc;
addpath(genpath('/home/ajoshi/projects/svreg/src'));
addpath(genpath('/home/ajoshi/projects/svreg/3rdParty'));
addpath(genpath('/home/ajoshi/projects/svreg/MEX_Files'));

%v1=load_untouch_nii('/home/ajoshi/Downloads/HIGH_MOTION/HIGH_MOTION_t2_trufi_cor_20211001115157_23.nii');%('/home/ajoshi/Desktop/tmp/haste.nii.gz');
v1=load_untouch_nii('high_orig_bst.nii.gz');%('/home/ajoshi/Desktop/tmp/haste.nii.gz');

v1.img = double(v1.img);

im_sz_x = size(v1.img,1);im_sz_z = size(v1.img,3);


vout=v1;
[Tx,Ty]=meshgrid(1:im_sz_x,1:im_sz_z);

for j = 1:size(v1.img,2)
    Tx_full{j} = Tx;Ty_full{j}=Ty;
end

for dejitter=1:10
    %v1=vout;
    v1_rescaled=255*(vout.img/max(vout.img(:)));

    for j = 2:size(v1.img,2)-1

        I1 = v1_rescaled(:,[j-1,j+1],:); I1=permute(I1,[1,3,2]);
        I2 = squeeze(v1_rescaled(:,j,:));

        I1r(:,:,1)=imresize(I1(:,:,1),[128,128]);I1r(:,:,2)=imresize(I1(:,:,2),[128,128]);
        I2r(:,:,1)=imresize(I2(:,:,1),[128,128]);I2r(:,:,2)=I2r(:,:,1);
        tic;
        [Iw,Tx,Ty] = demon_image_registration_mri(I1r,I2r);
        toc;
        Tx = im_sz_x*Tx/128;Ty = im_sz_z*Ty/128;
        Tx_full{j} = imresize(interp2(Tx_full{j},Tx,Ty),size(v1.img,[1,3]));
        Ty_full{j} = imresize(interp2(Ty_full{j},Tx,Ty),size(v1.img,[1,3]));

        IW=interp2(squeeze(v1.img(:,j,:)),Tx_full{j},Ty_full{j},'cubic');
        vout.img(:,j,:)=IW;


        fprintf('=====================%d/%d==%d/%d======================',j,size(v1.img,2),dejitter,10);
        close all;
    end

    save_untouch_nii_gz(vout,sprintf('high_motion3_128_dejitter_%d.nii.gz',dejitter));

end

