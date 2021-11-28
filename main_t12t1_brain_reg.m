%% Intra-modal rigid registration example
clc; close all; clear;
restoredefaultpath;      % To remove conflicting libraries. May remove this line.
addpath(genpath('/home/ajoshi/projects/lowfieldmri/src/register_files_affine_v12'))

t1_mov = '/home/ajoshi/projects/lowfieldmri/data/3T_alignment/V1_3T_1st_scan_MPRAGE.nii.gz';
t1_tar = '/home/ajoshi/projects/lowfieldmri/data/3T_alignment/V1_3T_2nd_scan_MPRAGE.nii.gz';
t1_warped = 'warped.nii.gz';

t1_mov_bse = '/home/ajoshi/projects/lowfieldmri/data/3T_alignment/V1_3T_1st_scan_MPRAGE.bse.nii.gz';
t1_tar_bse = '/home/ajoshi/projects/lowfieldmri/data/3T_alignment/V1_3T_2nd_scan_MPRAGE.bse.nii.gz';

t1_mov_bfc = '/home/ajoshi/projects/lowfieldmri/data/3T_alignment/V1_3T_1st_scan_MPRAGE.pvc.frac.nii.gz';
t1_tar_bfc = '/home/ajoshi/projects/lowfieldmri/data/3T_alignment/V1_3T_2nd_scan_MPRAGE.pvc.frac.nii.gz';

opts = struct(...
    'dof', 6, ...
    'pngout', false,   ...
    'nthreads', 2     ... Number of (possible) parallel threads to use
    );

opts.similarity='sd';

output_filename = 'warped_bfp.nii.gz';
output_file = 'warped.nii.gz';


[M_world, ref_loc, x_param] = register_files_affine(t1_mov_bfc, t1_tar_bfc, output_filename, opts);

reg_mat_file = [remove_extension(output_filename) '.rigid_registration_result.mat'];

transform_data_affine(t1_mov, 'moving', output_file, t1_mov_bfc, t1_tar_bfc, reg_mat_file, 'cubic');

