"""
SVR reconstructions for different combinations of stacks
Need to start docker demon using the following command as a non-root user:
systemctl --user start docker
"""

import os
import glob


def svr(subdir, template, mask, outsvr_dir, outsvr, res=1.0, slice_thickness=6.0):

    stacks_all = glob.glob(subdir + "/*.nii.gz")

    # remove files with mask in the name
    stacks_all = [x for x in stacks_all if "mask" not in x]

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

    phase = 10
    for ds_ratio in [1, 2, 4, 6, 8]:

        res = 1.0
        subdir = f"/deneb_disk/disc_mri/for_Ye_Heart_07_26_2024/nifti_files_experiments/phase_{phase+1:02}_rot_downsampled{ds_ratio}"
        template = f"/deneb_disk/disc_mri/for_Ye_Heart_07_26_2024/nifti_files_experiments/phase_11_rot_downsampled{ds_ratio}/p66_cardiac_multi_slice_multi_res_real_time_spiral_ssfp_ga_downsampled{ds_ratio}.nii.gz"
        mask = f"/deneb_disk/disc_mri/for_Ye_Heart_07_26_2024/nifti_files_experiments/phase_11_rot_downsampled{ds_ratio}/p66_cardiac_multi_slice_multi_res_real_time_spiral_ssfp_ga.mask_downsampled{ds_ratio}.nii.gz"
        outsvr = f"svr_heart_phase_{phase+1}_res_{res:.1f}_downsampled{ds_ratio}.nii.gz"
        outsvr_dir = "/deneb_disk/disc_mri/for_Ye_Heart_07_26_2024/outsvr_pad_experiments"

        svr(subdir, template, mask, outsvr_dir, outsvr, res=res, slice_thickness=6.0)


# End of main_svr.py
