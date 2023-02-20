clc;clear all;close all;restoredefaultpath;
%addpath(genpath('/big_disk/ajoshi/coding_ground/bfp/supp_data'))
addpath(genpath('/home/ajoshi/projects/bfp/src'));
%    1050345 rest 2

% Set the input arguments
configfile='/home/ajoshi/projects/disc_mri/pns_device_fmri/Feb_2023_scans_analysis/config_aaj.ini';

t1='/deneb_disk/PNS_fMRI/PNS_fMRI/PNS_FMRI_20230215/vol562_nii/6_t1_mprage_sag_11_nd.nii.gz';
fmri='/deneb_disk/PNS_fMRI/PNS_fMRI/PNS_FMRI_20230215/vol562_nii/10_ep2d_bold_4mm_tr3000_pns_left_off.nii.gz';

%fmri='/home/ajoshi/Downloads/BFP_issues/ACTL005/ACTL005.BOLD.resting.nii.gz';
studydir='/deneb_disk/PNS_fMRI/PNS_fMRI/PNS_FMRI_20230215/bfpout';
subid='vol562';
sessionid='10_ep2d_bold_4mm_tr3000_pns_left_off';
TR='';
 
% Call the bfp function
bfp(configfile, t1, fmri, studydir, subid, sessionid,TR);

%bfp.sh config.ini input/sub08001/anat/mprage_anonymized.nii.gz /big_disk/ajoshi/bfp_sample/input/sub08001/func/rest.nii.gz /big_disk/ajoshi/bfp_sample/output sub11 rest 2
