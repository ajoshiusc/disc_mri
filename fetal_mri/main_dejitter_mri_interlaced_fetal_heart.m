clear all;close all;clc;
addpath(genpath('/home/ajoshi/projects/svreg/src'));
addpath(genpath('/home/ajoshi/projects/svreg/3rdParty'));
addpath(genpath('/home/ajoshi/projects/svreg/MEX_Files'));

v1=load_untouch_nii('/ImagePTE1/ajoshi/data/disc_data/FETAL_HEART/FETAL_HEART_t2_trufi_cardiac_axial_4ch_lowSAR_50p_20211001115157_46.nii');

v1.img = double(v1.img);

im_sz_x = size(v1.img,1);im_sz_y = size(v1.img,2);


vout=v1;
[Tx,Ty]=meshgrid(1:im_sz_x,1:im_sz_y);

for j = 1:size(v1.img,3)
    Tx_full{j} = Tx;Ty_full{j}=Ty;
end

for dejitter=1:10
    %v1=vout;
    v1_rescaled=255*(vout.img/max(vout.img(:)));

    for j = 2:size(v1.img,3)-1

        I1 = v1_rescaled(:,:,[j-1,j+1]); %I1=permute(I1,[2,3,1]);
        I2 = squeeze(v1_rescaled(j,:,:));

        I1r(:,:,1)=imresize(I1(:,:,1),[256,256]);I1r(:,:,2)=imresize(I1(:,:,2),[256,256]);
        I2r(:,:,1)=imresize(I2(:,:,1),[256,256]);I2r(:,:,2)=I2r(:,:,1);
        tic;
        [Iw,Tx,Ty] = demon_image_registration_mri(I1r,I2r,3);
        toc;
        Tx = im_sz_x*Tx/256;Ty = im_sz_y*Ty/256;
        Tx_full{j} = imresize(interp2(Tx_full{j},Tx,Ty),size(v1.img,1:2));
        Ty_full{j} = imresize(interp2(Ty_full{j},Tx,Ty),size(v1.img,1:2));

        IW=interp2(squeeze(v1.img(:,:,j)),Tx_full{j},Ty_full{j},'cubic');
        vout.img(:,:,j)=IW;


        fprintf('=====================%d/%d==%d/%d======================',j,size(v1.img,3),dejitter,10);
        close all;
    end

    save_untouch_nii_gz(vout,sprintf('fetal_heart_alpha3_interlaced_dejitter_%d.nii.gz',dejitter));

end

