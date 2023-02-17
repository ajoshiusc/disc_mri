clc;clear all;close all;restoredefaultpath;
%addpath(genpath('/big_disk/ajoshi/coding_ground/bfp/supp_data'))
addpath(genpath('/home/ajoshi/projects/bfp/src'));
%    1050345 rest 2

% Set the input arguments
configfile='/deneb_disk/low_field_pns_device_fmri/config_aaj.ini';

t1='/deneb_disk/low_field_pns_device_fmri/PNS_FMRI_0822_nifti/6_t1_mprage_sag.nii.gz';
fmri='/deneb_disk/low_field_pns_device_fmri/11_16_2022/nii_files/5_ep2d_bold_4mm_tr3000_active_10min_sensation_stopped_halfway.nii.gz';

%fmri='/home/ajoshi/Downloads/BFP_issues/ACTL005/ACTL005.BOLD.resting.nii.gz';
studydir='/deneb_disk/low_field_pns_device_fmri/bfp_out';
subid='PNS_1116_active_10min_sensation_stopped_halfway';
sessionid='rest';
TR='3';
 
% Call the bfp function
bfp(configfile, t1, fmri, studydir, subid, sessionid,TR);

%bfp.sh config.ini input/sub08001/anat/mprage_anonymized.nii.gz /big_disk/ajoshi/bfp_sample/input/sub08001/func/rest.nii.gz /big_disk/ajoshi/bfp_sample/output sub11 rest 2
