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
    nsub = 5

    cmds_all = list()

    nsub = 5
    param_list = {"1e-14", "2e-14"}

    for sess, n, param in product((1, 2), range(1, nsub + 1), param_list):
        sub_nii = glob.glob(
            "/deneb_disk/3T_vs_low_field/justins_recons/low_field_mprage_data/subj"
            + str(n)
            + "_vol"
            + str(sess)
            + "/"
            + param
            + "/*.nii"
        )[0]
        out_dir = (
            "/deneb_disk/3T_vs_low_field/justins_recons/low_field_mprage_data_BrainSuite_4bfc/subj"
            + str(n)
            + "_vol"
            + str(sess)
            + "/"
            + param
        )

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

        new_data = np.minimum(200.0 * data / p, 255)

        new_img = nib.Nifti1Image(new_data, img.affine, img.header, dtype=np.uint16)

        new_img.to_filename(out_file)

        cmd = (
            "/home/ajoshi/Software/BrainSuite23a/bin/brainsuite_anatomical_pipeline_4bfc.sh "
            + out_file
        )
        # os.system(cmd)

        cmds_all.append(cmd)

    pool = Pool(processes=4)

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
