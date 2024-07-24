"""
SVR reconstructions for different combinations of stacks
"""

import os
import glob
import random


def svr(subdir, template, mask, outsvr_dir, outsvr, res=1.0, slice_thickness=8.0):

    stacks_all = glob.glob(subdir + "/*.nii.gz")

    stacks = ""
    num_stacks = random.randint(1, len(stacks_all))
    for j in range(num_stacks):
        stacks += " " + stacks_all[j]

    str_th = str(slice_thickness)

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
    docker_cmd = f"docker run --rm --mount type=bind,source=/deneb_disk,target=/deneb_disk fetalsvrtk/svrtk /bin/bash -lic 'cd {subdir}; {cmd}'"
    print(docker_cmd)
    os.system(docker_cmd)


if __name__ == "__main__":

    for phase in range(25):

        res = 2.0
        subdir = f"/deneb_disk/disc_mri/for_Ye_7_18_2024/25_phase_data/nifti_phase_{phase+1:02}_rot"
        template = glob.glob(subdir + "/*.nii.gz")[0]
        mask = "/deneb_disk/disc_mri/for_Ye_7_18_2024/25_phase_data/common_mask.nii.gz"
        outsvr = f"svr_heart_phase_{phase+1}_res_{res:.1f}.nii.gz"
        outsvr_dir = "/deneb_disk/disc_mri/for_Ye_7_18_2024/25_phase_data/outsvr"

        svr(subdir, template, mask, outsvr_dir, outsvr, res=1.0, slice_thickness=8.0)


# End of main_svr.py
