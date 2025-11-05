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
    indices = sorted(random.sample(range(n), r))
    return tuple(pool[i] for i in indices)


def run_svr(subj, te, subdir,  outsvr_dir, outsvr, res=1.0, slice_thickness=3.0, MAX_COMB=5):
    """
    This function runs the SVR reconstruction for a given subject, TE and directory.
    """
    mask = os.path.basename(glob.glob(subdir + f"/p*{subj}*te{te}*.mask.*")[0])
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
                str_stacks += " " + os.path.basename(s)
                str_th += " " + str(slice_thickness)

            outsvr = f"{outsvr_dir}/svr_te{te}_{subj}_numstacks_{num_stacks}_iter_{ns}.nii.gz"


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
    full_cmd = 'sbatch '+ '/project2/ajoshi_27/GitHub/disc_mri/mycmd.sh "' + docker_cmd +"\""
    print(full_cmd)
    #os.system(full_cmd)



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
    full_cmd = 'sbatch '+ '/project2/ajoshi_27/GitHub/disc_mri/mycmd.sh "' + docker_cmd +"\""
    print(full_cmd)
    os.system(full_cmd)



subj = "42_t2_haste"
subdir = "/project2/ajoshi_27/data/disc_mri/scan_10_23_2025/nifti_rot"
template = subdir + "/p42_t2_haste_tra_head_te98_p.nii.gz"
mask = subdir + "/p42_t2_haste_tra_head_te98_p.mask.nii.gz"



te = 98

stacks_all = glob.glob(subdir + f"/*head*te{te}*p.nii.gz")
res = 1
th = 3
MAX_COMB = 20
outsvr_dir = "/project2/ajoshi_27/data/disc_mri/scan_10_23_2025/outsvr"

for num_stacks in (3, 6, 9, 10):  # range(1, len(stacks_all) + 1):
    for ns in range(MAX_COMB):
        stacks = random_combination(stacks_all, num_stacks)

        str_stacks = ""
        str_th = ""

        for s in stacks:
            str_stacks += " " + s
            str_th += " " + str(th)

        outsvr = f"svr_te{te}_numstacks_{num_stacks}_iter_{ns}.nii.gz"

        if os.path.isfile(f"{outsvr_dir}/" + outsvr):
            continue

        run_svr(subj, te, subdir, outsvr_dir, outsvr, res=res, slice_thickness=th, MAX_COMB=MAX_COMB)


        """cmd = (
            f"cd {outsvr_dir}; mirtk reconstruct "
            + outsvr
            + " "
            + str(num_stacks)
            + str_stacks
            + " --resolution "
            + str(res)
        )

        cmd += " --thickness" + str_th + " --template " + template + " --mask " + mask

        print(cmd)
        # os.system(cmd)
        docker_cmd = f"docker run --rm --mount type=bind,source=/deneb_disk,target=/deneb_disk fetalsvrtk/svrtk /bin/bash -lic 'cd {subdir}; {cmd}'"
        print(docker_cmd)
        #os.system(docker_cmd)
        """
