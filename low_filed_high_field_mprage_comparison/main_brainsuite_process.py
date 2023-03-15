import os
import glob
import nibabel as nib
import numpy as np



nsub = 5
sess = 1

for n in range(1,nsub+1):
    sub_nii = glob.glob('/deneb_disk/low_field_mprage_data/subj' + str(n) + '_vol' + str(sess) + '/*.nii')[0]
    out_dir = '/deneb_disk/low_field_mprage_data/BrainSuite/subj' + str(n) + '_vol' + str(sess) 
    
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    
    out_file = out_dir + '/T1.nii.gz'

    img = nib.load(sub_nii)
    data = img.get_fdata()

    p = np.percentile(data, 95)
    print(f' max : {data.max()} and min : {data.min()} and 95 percentile: {p}') # doctest: +SKIP 3237.0
    new_data = data.copy()

    new_data = np.minimum(200.0*data/p,255)
    

    new_img = nib.Nifti1Image(new_data, img.affine, img.header)

    new_img.to_filename(out_file)
    type(new_img)




