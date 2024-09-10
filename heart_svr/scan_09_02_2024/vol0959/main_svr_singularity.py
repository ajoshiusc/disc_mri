"""
SVR reconstructions for different combinations of stacks
"""

import os
import glob
from itertools import product


def svr(subdir, template, mask, outsvr_dir, outsvr, res=1.0, slice_thickness=6.0):

    stacks_all = glob.glob(subdir + "/*.nii.gz")

    stacks = ""
    num_stacks = len(stacks_all)
    
    #print("*********************************")
    #print(num_stacks)
    #print("*********************************")

    if num_stacks != 4:
        print("Number of stacks is not 4 Check!!")
        print(stacks_all)
        return

    str_th = ""

    for j in range(num_stacks):
        stacks += " " + stacks_all[j]
        str_th += " " + str(slice_thickness)

    cmd = (
        f"cd {outsvr_dir}; mirtk reconstruct "
        + outsvr
        + " "
        + str(num_stacks)
        + stacks
        + " --resolution "
        + str(res)
    )

    cmd += " --thickness " + str_th + " --template " + template + " --mask " + mask

    #print(cmd)
    # os.system(cmd)
    docker_cmd = f"singularity run --bind /project/ajoshi_27 /scratch1/ajoshi/svrtk_latest.sif /bin/bash -lic \\\"{cmd}\\\" "
    #print(docker_cmd)
    full_cmd = 'sbatch '+ 'mycmd.sh "' + docker_cmd +"\""
    print(full_cmd)
    os.system(full_cmd)


if __name__ == "__main__":


    scans_dir_top = "/project/ajoshi_27/disc_mri/heart_svr_acquisition_08_22_2024/vol0950/nifti_files"
    expmt_dir_all = [scans_dir_top]

    for phase, expmt_dir in product(range(25), expmt_dir_all):

        res = 1.0
        subdir = expmt_dir + f"/phase_{phase+1:02}_rot"
        template = "/project/ajoshi_27/disc_mri/heart_svr_acquisition_08_22_2024/vol0950/common_template/p60_cardiac_svr_sweep_1_res_15.pad.nii.gz"
        mask = "/project/ajoshi_27/disc_mri/heart_svr_acquisition_08_22_2024/vol0950/common_template/p60_cardiac_svr_sweep_1_res_15.pad.dilated2.mask.nii.gz"

        outsvr = (
            f"svr_heart_"
            + expmt_dir.split("/")[-1]
            + f"_phase_{phase+1:02}_res_{res:.1f}.nii.gz"
        )
        outsvr_dir = "/project/ajoshi_27/disc_mri/heart_svr_acquisition_08_22_2024/vol0950/outsvr_pad2"

        #expdir_prefix = expmt_dir.split("/")[-1]
        outsvr_dir = "/project/ajoshi_27/disc_mri/heart_svr_acquisition_08_22_2024/vol0950/outsvr_pad2/" + f"phase_{phase+1:02}_allstacks"

        os.makedirs(outsvr_dir)

        thickness = 6.0

        # convert thickness to float
        thickness = float(thickness)

        svr(
            subdir,
            template,
            mask,
            outsvr_dir,
            outsvr,
            res=res,
            slice_thickness=thickness,
        )


# End of main_svr.py
