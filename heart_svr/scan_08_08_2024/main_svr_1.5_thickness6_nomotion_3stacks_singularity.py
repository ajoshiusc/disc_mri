"""
SVR reconstructions for different combinations of stacks
"""

import os
import glob
from itertools import product


def svr(subdir, template, mask, outsvr_dir, outsvr, res=1.0, slice_thickness=6.0):

    stacks_all = glob.glob(subdir + "/*.nii.gz")

    # if the list of stacks contains p61 as a substring, delete that from the list
    for stack in stacks_all:
        if "p61" in stack:
            stacks_all.remove(stack)



    ## remove stack61 from the list. We want to keep stack60 based on Ye's suggestion
    #if "p61" in stacks_all:
    #    stacks_all.remove("p61")

    stacks = ""
    num_stacks = len(stacks_all)

    if num_stacks != 3:
        print("Number of stacks is not 3 Check!!")
        print(num_stacks)
        return

    for j in range(num_stacks):
        stacks += " " + stacks_all[j]

    str_th = ""

    for j in range(num_stacks):
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

    print(cmd)
    # os.system(cmd)
    docker_cmd = f"singularity run --bind /project/ajoshi_27 /scratch1/ajoshi/svrtk_latest.sif /bin/bash -lic \\\"cd {subdir}; {cmd}\\\" "
    #print(docker_cmd)
    full_cmd = 'sbatch '+ 'mycmd.sh "' + docker_cmd +"\""
    print(full_cmd)
    os.system(full_cmd)


if __name__ == "__main__":

    expmt_dir_all = [
        "/project/ajoshi_27/disc_mri/heart_svr_acquisition_08_08_2024/nifti_files/res_1.5_thickness_6"
    ]  # glob.glob(scans_dir_top + "/*")

    for phase, expmt_dir in product(range(25), expmt_dir_all):

        res = 1.0
        subdir = expmt_dir + f"/phase_{phase+1:02}_rot"
        template = "/project/ajoshi_27/disc_mri/heart_svr_acquisition_08_08_2024/common_template/p65_cardiac_svr_sweep_2_res_12.pad.nii.gz"
        mask = "/project/ajoshi_27/disc_mri/heart_svr_acquisition_08_08_2024/common_template/p65_cardiac_svr_sweep_2_res_12.pad.dilated.mask.nii.gz"

        outsvr = (
            f"svr_heart_"
            + expmt_dir.split("/")[-1]
            + f"_phase_{phase+1:02}_res_{res:.1f}.nii.gz"
        )
        expdir_prefix = expmt_dir.split("/")[-1]        
        outsvr_dir = "/project/ajoshi_27/disc_mri/heart_svr_acquisition_08_08_2024/nifti_files_experiments/outsvr_pad_3stacks/" + f"phase_{phase+1:02}_expt_{expdir_prefix}"

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
