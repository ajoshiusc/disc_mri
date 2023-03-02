clc;clear all;close all;

dicom_file = '/deneb_disk/chla_data_2_21_2023/unzipped_dicomms/SVR010/Mri_Fetal__Pelvic - MRIFETAL/BRAIN_SAG_SSh_TSE_esp56_1201/IM-0269-0001.dcm'
%'/home/ajoshi/projects/disc_mri/clinical_svr_study/SVR_3D_DICOM/SVR010_SVR_3D/IM_0044';

nii_file = '/home/ajoshi/projects/disc_mri/clinical_svr_study/SVR_3D_NIFTI/SVR010_SVR.nii.gz';

write_dir = '/home/ajoshi/projects/disc_mri/clinical_svr_study/SVR010_dcm_output/'
write_name = 'IM'
dinfo = dicominfo(dicom_file);
im_all = niftiread(nii_file);
para = niftiinfo(nii_file);
%% correct some time
%load(recon_file)
nslice = size(im_all, 3);
SeriesTime = str2double(dinfo.SeriesTime);

% %% correct some slice location
% q0 = para.kspace_info.user_QuaternionW;
% q1 = para.kspace_info.user_QuaternionX;
% q2 = para.kspace_info.user_QuaternionY;
% q3 = para.kspace_info.user_QuaternionZ;
% rot = [2 * (q0^2 + q1^2 ) - 1,   2 * (q1*q2 - q0*q3),    2 * (q1*q3 + q0*q2);
%     2 * (q1*q2 + q0*q3),     2 * (q0^2 + q2^2 ) - 1,  2 * (q2*q3 - q0*q1);
%     2 * (q1*q3 - q0*q2),     2 * (q2*q3 + q0*q1),    2 * (q0^2 + q3^2) - 1];

rot = eye(3);

x0 = dinfo.ImagePositionPatient(1);
y0 = dinfo.ImagePositionPatient(2);
z0 = dinfo.ImagePositionPatient(3);

SliceGap = para.PixelDimensions(3); % para.kspace_info.user_SliceGap;

SliceShifts = ((1:nslice) - floor(nslice / 2) - 1) * SliceGap;
% SliceShifts = ((1:nslice) - 1) * SliceGap;
SliceShiftsRot = rot * [zeros(2, nslice); SliceShifts];

%% write dicom
im_all = int16(im_all * 32767 / max(im_all(:)));
time_per_slice = 1 %TBD para.kspace_info.user_TR * para.Recon.narm / 1000 / 1000; % [sec]

SliceLocation0          = dinfo.SliceLocation;
ImagePositionPatient0   = dinfo.ImagePositionPatient;

nframe = 1;

dinfo.SeriesNumber = dinfo.SeriesNumber + 10000;

for i = 1:nslice
    for j = 1:nframe
        warning off
        AcquisitionTime         = num2str(round((SeriesTime + time_per_slice * j + (i - 1) * nframe * time_per_slice) * 1000) / 1000);
        ContentTime             = AcquisitionTime;
        ImagesInAcquisition     = nslice * nframe;
        InstanceNumber          = j + (i - 1) * nframe;
        FrameTime               = time_per_slice * 1000;
        SliceLocation           = SliceLocation0 + SliceShifts(i);
        ImagePositionPatient    = ImagePositionPatient0 + SliceShiftsRot(:, i);
        
        dinfo.AcquisitionTime       = AcquisitionTime;
        dinfo.ContentTime           = ContentTime;
        dinfo.ImagesInAcquisition   = ImagesInAcquisition;
        dinfo.InstanceNumber        = InstanceNumber;
        dinfo.FrameTime             = FrameTime;
        dinfo.SliceLocation         = SliceLocation;
        dinfo.ImagePositionPatient  = ImagePositionPatient;

        dinfo.PixelSpacing = [1,1];
        
        file_name = sprintf('%s%s_slice_%03g.dcm', write_dir, write_name, i);
        dinfo.SeriesDescription = 'SVR Recon';
        dicomwrite(im_all(:, :, i)', file_name, dinfo);
    end
end