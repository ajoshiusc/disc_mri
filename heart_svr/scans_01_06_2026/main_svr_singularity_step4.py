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
    docker_cmd = f"apptainer run --bind /project2/ajoshi_27 /scratch1/ajoshi/svrtk_latest.sif /bin/bash -lic \\\"{cmd}\\\" "
    #print(docker_cmd)
    full_cmd = 'sbatch '+ '/project2/ajoshi_27/GitHub/disc_mri/heart_svr/scans_01_06_2026/mycmd.sh "' + docker_cmd +"\""
    print(full_cmd)
    os.system(full_cmd)


if __name__ == "__main__":


    #scans_dir_top = "/project/ajoshi_27/disc_mri/heart_svr_acquisition_10_26_2024/nifti_files"
    #expmt_dir_all = glob.glob(scans_dir_top + "/vol0929*")

    scans_dir_top =  '/project2/ajoshi_27/data/heart_svr/heart_svr_acquisition_01_06_2026/nifti_files'
    expmt_dir_all = glob.glob(scans_dir_top + "/vol*")

    for phase, expmt_dir in product(range(25), expmt_dir_all):

        expt_name = expmt_dir[-16:]
        res = 1.0
        subdir = expmt_dir + f"/phase_{phase+1:02}_rot"

        tname = glob.glob(f"/project2/ajoshi_27/data/heart_svr/heart_svr_acquisition_01_06_2026/{expt_name}_template/p*_cardiac_svr_sweep_1_res_*.pad.nii.gz")[0]
        template =  tname
        mask = tname[:-7] + ".dilated.mask.nii.gz"
        #"/project2/ajoshi_27/data/heart_svr/{expt_name}_template/p59_cardiac_svr_sweep_1_res_15.pad.dilated.mask.nii.gz"

        outsvr = (
            f"svr_heart_"
            + expmt_dir.split("/")[-1]
            + f"_phase_{phase+1:02}_res_{res:.1f}.nii.gz"
        )

        # if outsvr file already exists, skip
        outsvr_fullpath = f"/project2/ajoshi_27/data/heart_svr/heart_svr_acquisition_01_06_2026/outsvr_pad/{expmt_dir.split('/')[-1]}/phase_{phase+1:02}_allstacks/{outsvr}"

        if os.path.isfile(outsvr_fullpath):
            print("SVR output file already exists, skipping:", outsvr_fullpath)
            continue
        
        expdir_prefix = expmt_dir.split("/")[-1]
        outsvr_dir = f"/project2/ajoshi_27/data/heart_svr/heart_svr_acquisition_01_06_2026/outsvr_pad/{expdir_prefix}/" + f"phase_{phase+1:02}_allstacks"

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
