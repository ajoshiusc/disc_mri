"""
SVR reconstructions for different combinations of stacks
"""

import os
import glob
import random


def random_combination(iterable, r):
    "Random selection from itertools.combinations(iterable, r)"
    pool = tuple(iterable)
    n = len(pool)
    print(n,r)
    indices = sorted(random.sample(range(n), r))
    return tuple(pool[i] for i in indices)


def run_svr(subj, te, subdir,  outsvr_dir, res=1.0, slice_thickness=3.0, MAX_COMB=5):
    """
    This function runs the SVR reconstruction for a given subject, TE and directory.
    """
    mask = glob.glob(subdir + f"/p*{subj}*te{te}*.mask.*")[0]
    template = mask[:-12] + ".nii.gz"

    stacks_all = glob.glob(subdir + f"/p*{subj}*te{te}*p.nii.gz")


    for num_stacks in range(1, len(stacks_all) + 1):
        for ns in range(MAX_COMB):
            stacks = random_combination(stacks_all, num_stacks)

            if ns > MAX_COMB:
                continue

            str_stacks = ""
            str_th = ""

            for s in stacks:
                str_stacks += " " + s #os.path.basename(s)
                str_th += " " + str(slice_thickness)

        
            outsvr_final = f"{outsvr_dir}/svr_te{te}_{subj}_numstacks_{num_stacks}_iter_{ns}.nii.gz"

            if os.path.exists(outsvr_final):
                print(f"File {outsvr_final} exists. Skipping...")
                continue
            
            # make a temp directory inside outsvr_dir and set outsvr based on that
            outsvr = f"svr_te{te}_{subj}_numstacks_{num_stacks}_iter_{ns}.nii.gz"
            outsvr_dir_temp = f"{outsvr_dir}/temp_svr_te{te}_{subj}_numstacks_{num_stacks}_iter_{ns}"
            if not os.path.exists(outsvr_dir_temp):
                os.makedirs(outsvr_dir_temp)
            outsvr = f"{outsvr_dir_temp}/{outsvr}"




            cmd = (
                f"cd {outsvr_dir_temp}; mirtk reconstruct "
                + outsvr
                + " "
                + str(num_stacks)
                + str_stacks
                + " --resolution "
                + str(res)
            )

            cmd += " --thickness " + str_th + " --template " + template + " --mask " + mask

            cmd += "; cp " + outsvr + " " + outsvr_final + " "
            #print(cmd)
            # os.system(cmd)
            docker_cmd = f"apptainer run --bind /project2/ajoshi_27 /scratch1/ajoshi/svrtk_latest.sif /bin/bash -lic \\\"{cmd}\\\" "
            #print(docker_cmd)
            full_cmd = 'sbatch '+ '/project2/ajoshi_27/GitHub/disc_mri/mycmd.sh "' + docker_cmd +"\""
            print(full_cmd)
            os.system(full_cmd)
            
            


if __name__ == "__main__":
    subj = "_t2_haste"
    subdir = "/project2/ajoshi_27/data/disc_mri/scan_2_6_2026/nifti_rot"
    te = 98

    res = 1
    th = 3
    MAX_COMB = 20
    outsvr_dir = "/project2/ajoshi_27/data/disc_mri/scan_2_6_2026/outsvr"

    run_svr(subj, te, subdir, outsvr_dir, res=res, slice_thickness=th, MAX_COMB=MAX_COMB)

