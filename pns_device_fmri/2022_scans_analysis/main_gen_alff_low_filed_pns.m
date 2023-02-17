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

anatbase='/deneb_disk/low_field_pns_device_fmri/bfp_out/PNS_1116_active_10min_sensation_stopped_halfway/anat/PNS_1116_active_10min_sensation_stopped_halfway_T1w';
fmribase='/deneb_disk/low_field_pns_device_fmri/bfp_out/PNS_1116_active_10min_sensation_stopped_halfway/func/PNS_1116_active_10min_sensation_stopped_halfway_rest_bold';



%function gen_alff_gord()
get_alff_gord(config, fmribase, anatbase);

gen_brainordinates_alff('/home/ajoshi/BrainSuite21a', anatbase, fmribase, 'ALFF_Z');
gen_brainordinates_alff('/home/ajoshi/BrainSuite21a', anatbase, fmribase, 'ALFF');
gen_brainordinates_alff('/home/ajoshi/BrainSuite21a', anatbase, fmribase, 'fALFF');