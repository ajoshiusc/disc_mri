%% Intra-modal rigid registration example
clc; close all; clear;
restoredefaultpath;      % To remove conflicting libraries. May remove this line.
addpath(genpath('/home/ajoshi/projects/lowfieldmri/src/register_files_affine_v12'))

t1_mov = '/home/ajoshi/projects/lowfieldmri/data/3T_alignment/V1_3T_1st_scan_MPRAGE.nii.gz';
t1_tar = '/home/ajoshi/projects/lowfieldmri/data/3T_alignment/V1_3T_2nd_scan_MPRAGE.nii.gz';


% Run BrainSuite upto 'Tissue classification on the input T1 MRI files. This will generate pvc frac file.
t1_mov_pvcfrac = '/home/ajoshi/projects/lowfieldmri/data/3T_alignment/V1_3T_1st_scan_MPRAGE.pvc.frac.nii.gz';
t1_tar_pvcfrac = '/home/ajoshi/projects/lowfieldmri/data/3T_alignment/V1_3T_2nd_scan_MPRAGE.pvc.frac.nii.gz';


% For rigid registration, set dof = 6
% For affine registration, set dof =12
opts = struct(...
    'dof', 6, ...
    'pngout', false,   ...
    'nthreads', 2     ... Number of (possible) parallel threads to use
    );

opts.similarity='sd';

output_filename = 'warped_pvcfrac.nii.gz';
output_file = 'warped_t1_mri.nii.gz'; % This is the final output file


[M_world, ref_loc, x_param] = register_files_affine(t1_mov_pvcfrac, t1_tar_pvcfrac, output_filename, opts);

reg_mat_file = [remove_extension(output_filename) '.rigid_registration_result.mat'];

transform_data_affine(t1_mov, 'moving', output_file, t1_mov_pvcfrac, t1_tar_pvcfrac, reg_mat_file, 'cubic');

