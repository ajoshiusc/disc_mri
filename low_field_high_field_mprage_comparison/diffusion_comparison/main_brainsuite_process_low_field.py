import os
import glob
import nibabel as nib
import numpy as np
import SimpleITK as sitk
from itertools import product

from multiprocessing import Pool



def regparfun(cmd_str):
    os.system(cmd_str)

    return True


def main():

    cmds_all = []

    for subid in range(1,6):

        sub_nii = f"/deneb_disk/3T_vs_low_field/FA_MD_for_common_space/MPRAGE/V{subid}_LF_mprage_vol1_recon_GNL.nii.gz"

        out_dir = f"/deneb_disk/3T_vs_low_field/FA_MD_for_common_space/MPRAGE_BrainSuite_4bfc/V{subid}_LF_mprage_vol1_recon_GNL"

        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)

        out_file = out_dir + "/T1.nii.gz"

        if os.path.isfile(out_dir + "/T1.roiwise.stats.txt"):
            continue
        else:
            print('Processing files in ' + out_dir)
            #continue
            


        img = nib.load(sub_nii)
        data = img.get_fdata()

        p = np.percentile(data, 98)
        print(
            f" max : {data.max()} and min : {data.min()} and 98 percentile: {p}"
        )  # doctest: +SKIP 3237.0
        new_data = data.copy()

        new_data = np.minimum(1000.0 * data / p, 1500)

        new_img = nib.Nifti1Image(new_data, img.affine, img.header, dtype=np.uint16)

        new_img.to_filename(out_file)

        cmd = (
            "/home/ajoshi/Software/BrainSuite23a/bin/brainsuite_anatomical_pipeline_4bfc.sh "
            + out_file
        )
        # os.system(cmd)

        cmds_all.append(cmd)

    pool = Pool(processes=3)

    #    regparfun(subsnotdone[2])

    print("++++++++++++++")
    pool.map(regparfun, cmds_all)
    print("++++SUBMITTED++++++")

    pool.close()
    pool.join()


if __name__ == "__main__":
    main()


"""     out_file = out_dir + '/T1.bse.nii.gz'

    input = sitk.ReadImage(out_file)
    image = sitk.Cast(input, sitk.sitkFloat32)
    # print(type(image))
    correctedImg = sitk.N4BiasFieldCorrection(image)

    out_file = out_dir + '/T1_N4.nii.gz'

    sitk.WriteImage(correctedImg, out_file) 

 """
