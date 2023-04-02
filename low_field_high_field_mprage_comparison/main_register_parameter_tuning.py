import os
import glob

target = '/deneb_disk/3T_vs_low_field/3T_mprage_data_BrainSuite/subj2_vol1/T1.nii.gz'
outdir = '/deneb_disk/3T_vs_low_field/registered_data_param_tuning'

subdirs = glob.glob('/deneb_disk/3T_vs_low_field/parameter_tuning/parameter_tuning_subj2_vo1_BrainSuite/*')

for subdir in subdirs:

    dir,param = os.path.split(subdir)
    sub_nii = subdir + '/T1.nii.gz'
    out_nii = outdir + '/' + 'T1'+param+'to_3T.nii.gz' 
    
    cmd = f'flirt -ref {target} -in {sub_nii} -out {out_nii}'
    os.system(cmd)




