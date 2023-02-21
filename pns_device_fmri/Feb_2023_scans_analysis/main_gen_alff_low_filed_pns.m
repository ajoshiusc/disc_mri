%clear all;close all;clc;
addpath(genpath('/home/ajoshi/projects/bfp/src'))
%fmribase = '/home/ajoshi/tmp_study_dir/sub08001/func/sub08001_rest_bold';
%anatbase = '/home/ajoshi/tmp_study_dir/sub08001/anat/sub08001_T1w';
config.FSLPATH = '/home/ajoshi/webware/fsl'
config.FSLOUTPUTTYPE='NIFTI_GZ';
config.AFNIPATH = '/home/ajoshi/abin';
config.FSLRigidReg=0;
config.MultiThreading=0;
config.BFPPATH='/home/ajoshi/projects/bfp';



%anatbase='/deneb_disk/low_field_pns_device_fmri/bfp_out_scan1/PNS_0822/anat/PNS_0822_T1w';
%fmribase='/deneb_disk/low_field_pns_device_fmri/bfp_out_scan1/PNS_0822/func/PNS_0822_task-restingstate_bold';

t1='/deneb_disk/PNS_fMRI/PNS_fMRI/PNS_FMRI_20230215/bfpout/vol562/anat/vol562_T1w.nii.gz';
fmri='/deneb_disk/PNS_fMRI/PNS_fMRI/PNS_FMRI_20230215/bfpout/vol562/func/vol562_10_ep2d_bold_4mm_tr3000_pns_left_off_bold.nii.gz';

anatbase=t1(1:end-7);
fmribase=fmri(1:end-7);


%function gen_alff_gord()
get_alff_gord(config, fmribase, anatbase);

gen_brainordinates_alff('/home/ajoshi/BrainSuite21a', anatbase, fmribase, 'ALFF_Z');
gen_brainordinates_alff('/home/ajoshi/BrainSuite21a', anatbase, fmribase, 'ALFF');
gen_brainordinates_alff('/home/ajoshi/BrainSuite21a', anatbase, fmribase, 'fALFF');