clear all;close all;clc;
addpath(genpath('/home/ajoshi/projects/svreg/src'));
addpath(genpath('/home/ajoshi/projects/svreg/3rdParty'));
addpath(genpath('/home/ajoshi/projects/svreg/MEX_Files'));

v1=load_untouch_nii('/home/ajoshi/Downloads/disc_data/fetal_mri/fetal_vol2_t2_haste_trufi/t2_haste_cor_TE119/_t2_haste_cor_TE119_20210915181625_9.nii');

v1_1.img = double(v1.img(:,:,1:2:end));
v1_2.img = double(v1.img(:,:,2:2:end));

im_sz_x = size(v1.img,1);im_sz_y = size(v1.img,2);


vout=v1;
vout.img = double(vout.img);

[Tx_1,Ty_1]=meshgrid(1:im_sz_x,1:im_sz_y);
[Tx_2,Ty_2]=meshgrid(1:im_sz_x,1:im_sz_y);

for j = 1:size(v1.img,3)
    Tx_full_1{j} = Tx_1;Ty_full_1{j}=Ty_1;
    Tx_full_2{j} = Tx_2;Ty_full_2{j}=Ty_2;
end

for dejitter=1:10
    %v1=vout;
    v1_rescaled_1=255*(vout.img(:,:,1:2:end)/max(vout.img(:)));
    v1_rescaled_2=255*(vout.img(:,:,2:2:end)/max(vout.img(:)));

    for j = 2:size(v1_1.img,3)-1

        I1_1 = v1_rescaled_1(:,:,[j-1,j+1]); %I1=permute(I1,[2,3,1]);
        I2_1 = squeeze(v1_rescaled_1(j,:,:));
        I1_2 = v1_rescaled_2(:,:,[j-1,j+1]); %I1=permute(I1,[2,3,1]);
        I2_2 = squeeze(v1_rescaled_2(j,:,:));

        I1r_1(:,:,1)=imresize(I1_1(:,:,1),[256,256]);I1r_1(:,:,2)=imresize(I1_1(:,:,2),[256,256]);
        I2r_1(:,:,1)=imresize(I2_1(:,:,1),[256,256]);I2r_1(:,:,2)=I2r_1(:,:,1);

        I1r_2(:,:,1)=imresize(I1_2(:,:,1),[256,256]);I1r_2(:,:,2)=imresize(I1_2(:,:,2),[256,256]);
        I2r_2(:,:,1)=imresize(I2_2(:,:,1),[256,256]);I2r_2(:,:,2)=I2r_2(:,:,1);



        tic;
        [Iw_1,Tx_1,Ty_1] = demon_image_registration_mri(I1r_1,I2r_1);
        [Iw_2,Tx_2,Ty_2] = demon_image_registration_mri(I1r_2,I2r_2);

        toc;
        Tx_1 = im_sz_x*Tx_1/256;Ty_1 = im_sz_y*Ty_1/256;
        Tx_2 = im_sz_x*Tx_2/256;Ty = im_sz_y*Ty_2/256;

        Tx_full_1{j} = imresize(interp2(Tx_full_1{j},Tx_1,Ty_1),size(v1.img,1:2));
        Ty_full_2{j} = imresize(interp2(Ty_full_2{j},Tx_2,Ty_2),size(v1.img,1:2));
        
        Tx_full_2{j} = imresize(interp2(Tx_full_2{j},Tx_2,Ty_2),size(v1.img,1:2));
        Ty_full_2{j} = imresize(interp2(Ty_full_2{j},Tx_2,Ty_2),size(v1.img,1:2));


        IW_1=interp2(squeeze(double(v1.img(:,:,j))),Tx_full_1{j},Ty_full_1{j},'cubic');
        vout.img(:,:,2*j-1)=IW_1;

        IW_2=interp2(squeeze(double(v1.img(:,:,j))),Tx_full_2{j},Ty_full_2{j},'cubic');
        vout.img(:,:,2*j)=IW_2;


        fprintf('=====================%d/%d==%d/%d======================',j,size(v1.img,3),dejitter,10);
        close all;
    end

    save_untouch_nii_gz(vout,sprintf('interlaced_alternating_1_2_dejitter_%d.nii.gz',dejitter));

end

