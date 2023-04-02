import os
import glob
import nibabel as nib
import numpy as np
import SimpleITK as sitk
from itertools import product

subdirs = glob.glob('/deneb_disk/3T_vs_low_field/parameter_tuning/parameter_tuning_subj2_vo1/*')


for subdir in subdirs:

    dir, param = os.path.split(subdir)

    sub_nii = glob.glob(subdir + '/*.nii')[0]
    out_dir = '/deneb_disk/3T_vs_low_field/parameter_tuning/parameter_tuning_subj2_vo1_BrainSuite/' + param 
    
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    
    out_file = out_dir + '/T1.nii.gz'

    img = nib.load(sub_nii)
    data = img.get_fdata()

    p = np.percentile(data, 98)
    print(f' max : {data.max()} and min : {data.min()} and 98 percentile: {p}') # doctest: +SKIP 3237.0
    new_data = data.copy()

    new_data = np.minimum(200.0*data/p,255)
    

    new_img = nib.Nifti1Image(new_data, img.affine, img.header,dtype=np.uint16)

    new_img.to_filename(out_file)

    cmd = '/home/ajoshi/BrainSuite21a/bin/brainsuite_anatomical_pipeline.sh ' + out_file
    os.system(cmd)




