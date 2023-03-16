import os
import glob
import nibabel as nib
import numpy as np
import SimpleITK as sitk


nsub = 5
sess = 1

for n in range(3,nsub+1):
    sub_nii = glob.glob('/deneb_disk/low_field_mprage_data/subj' + str(n) + '_vol' + str(sess) + '/*.nii')[0]
    out_dir = '/deneb_disk/low_field_mprage_data/BrainSuite/subj' + str(n) + '_vol' + str(sess) 
    
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    
    out_file = out_dir + '/T1.nii.gz'

    img = nib.load(sub_nii)
    data = img.get_fdata()

    p = np.percentile(data, 99.999)
    print(f' max : {data.max()} and min : {data.min()} and 98 percentile: {p}') # doctest: +SKIP 3237.0
    new_data = data.copy()

    new_data = np.minimum(200.0*data/p,255)
    

    new_img = nib.Nifti1Image(new_data, img.affine, img.header,dtype=np.uint16)

    new_img.to_filename(out_file)

    out_file = out_dir + '/T1.bse.nii.gz'

    input = sitk.ReadImage(out_file)
    image = sitk.Cast(input, sitk.sitkFloat32)
    # print(type(image))
    correctedImg = sitk.N4BiasFieldCorrection(image)

    out_file = out_dir + '/T1_N4.nii.gz'

    sitk.WriteImage(correctedImg, out_file) 




