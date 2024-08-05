import os
import glob
import nibabel as nib
import numpy as np
import SimpleITK as sitk
from itertools import product
from multiprocessing import Pool


""" 
    out_file = out_dir + '/T1.bse.nii.gz'

    input = sitk.ReadImage(out_file)
    image = sitk.Cast(input, sitk.sitkFloat32)
    # print(type(image))
    correctedImg = sitk.N4BiasFieldCorrection(image)

    out_file = out_dir + '/T1_N4.nii.gz'

    sitk.WriteImage(correctedImg, out_file) 

 """


def regparfun(cmd_str):
    os.system(cmd_str)

    return True


def main():

    sub_nii = "/deneb_disk/3T_vs_low_field/4_figures/hf/sub2_H1.nii.gz"
    out_dir = "/deneb_disk/3T_vs_low_field/4_figures/brainsuite_4bfc/hf"

    out_file = out_dir + "/T1.nii.gz"

    img = nib.load(sub_nii)
    data = img.get_fdata()

    p = np.percentile(data, 98)
    print(
        f" max : {data.max()} and min : {data.min()} and 98 percentile: {p}"
    )  # doctest: +SKIP 3237.0
    new_data = data.copy()

    new_data = np.minimum(200.0 * data / p, 255)

    new_img = nib.Nifti1Image(new_data, img.affine, img.header, dtype=np.uint16)

    new_img.to_filename(out_file)

    cmd = (
        "/home/ajoshi/Software/BrainSuite23a/bin/brainsuite_anatomical_pipeline_4bfc.sh "
        + out_file
    )
    os.system(cmd)


if __name__ == "__main__":
    main()
