%% Intra-modal rigid registration example
clc; close all; clear;
restoredefaultpath;      % To remove conflicting libraries. May remove this line.
addpath(genpath('/home/ajoshi/projects/lowfieldmri/src/register_files_affine_v12'))

% t1_mov is file that will be warped
% t1_tar i sthe files that will be used as a target

t1_mov = '/home/ajoshi/Downloads/Low_field/3ttop55t/3T_0.55T_MPRAGE/V1_LF_2nd_MPRAGE.nii.gz';
t1_tar = '/home/ajoshi/Downloads/Low_field/3ttop55t/3T_0.55T_MPRAGE/V1_3T_2nd_MPRAGE.nii.gz';

t1_mov_bfc = '/home/ajoshi/Downloads/Low_field/3ttop55t/3T_0.55T_MPRAGE/V1_LF_2nd_MPRAGE.bfc.nii.gz';
t1_tar_bfc = '/home/ajoshi/Downloads/Low_field/3ttop55t/3T_0.55T_MPRAGE/V1_3T_2nd_MPRAGE.bfc.nii.gz';


% For rigid registration, set dof = 6
% For affine registration, set dof =12
opts = struct(...
    'dof', 6, ...
    'pngout', false,   ...
    'nthreads', 2     ... Number of (possible) parallel threads to use
    );

opts.similarity='cr';

output_filename = 'warped_bfc.nii.gz';
output_file = 'warped_t1_mri.nii.gz'; % This is the final output file


[M_world, ref_loc, x_param] = register_files_affine(t1_mov_bfc, t1_tar_bfc, output_filename, opts);

reg_mat_file = [remove_extension(output_filename) '.rigid_registration_result.mat'];

transform_data_affine(t1_mov, 'moving', output_file, t1_mov_bfc, t1_tar_bfc, reg_mat_file, 'cubic');

