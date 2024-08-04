"""
SVR reconstructions for different combinations of stacks
"""

import os
import glob


def svr(subdir, template, mask, outsvr_dir, outsvr, res=1.0, slice_thickness=6.0):

    stacks_all = glob.glob(subdir + "/*.nii.gz")

    stacks = ""
    num_stacks = len(stacks_all)

    if num_stacks < 4:
        print("Number of stacks is not 4 Check!!")
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
    docker_cmd = f"docker run --rm --mount type=bind,source=/deneb_disk,target=/deneb_disk fetalsvrtk/svrtk /bin/bash -lic 'cd {subdir}; {cmd}'"
    print(docker_cmd)
    os.system(docker_cmd)


if __name__ == "__main__":

    for phase in range(25):

        res = 1.0
        subdir = f"/deneb_disk/disc_mri/for_Ye_Heart_07_26_2024/nifti_files/phase_{phase+1:02}_rot"
        template = "/deneb_disk/disc_mri/for_Ye_Heart_07_26_2024/nifti_files/common_template_mask/p66_cardiac_multi_slice_multi_res_real_time_spiral_ssfp_ga_pad.nii.gz"
        mask = "/deneb_disk/disc_mri/for_Ye_Heart_07_26_2024/nifti_files/common_template_mask/p66_cardiac_multi_slice_multi_res_real_time_spiral_ssfp_ga_pad.mask.nii.gz"
        outsvr = f"svr_heart_phase_{phase+1}_res_{res:.1f}.nii.gz"
        outsvr_dir = "/deneb_disk/disc_mri/for_Ye_Heart_07_26_2024/outsvr_pad"

        svr(subdir, template, mask, outsvr_dir, outsvr, res=res, slice_thickness=6.0)


# End of main_svr.py
