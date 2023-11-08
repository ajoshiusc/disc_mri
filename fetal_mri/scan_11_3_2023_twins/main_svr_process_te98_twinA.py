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


subdir = "/deneb_disk/disc_mri/scan_11_3_2023_twins_nii_rot"
template = "p47_t2_haste_cor_head_babya_te98_p.nii.gz"
mask = "p47_t2_haste_cor_head_babya_te98_p.mask.nii.gz"
twin_id = "A"

stacks_all = glob.glob(subdir + "/*head*te98_p.nii.gz")

res = 1
th = 3
MAX_COMB = 5


for num_stacks in range(1, len(stacks_all) + 1):
    for ns in range(MAX_COMB):
        stacks = random_combination(stacks_all, num_stacks)

        if ns > MAX_COMB:
            continue

        str_stacks = ""
        str_th = ""

        for s in stacks:
            str_stacks += " " + os.path.basename(s)
            str_th += " " + str(th)

        outsvr = f"svr_te98_twin{twin_id}_numstacks_{num_stacks}_iter_{ns}.nii.gz"

        if os.path.isfile('/deneb_disk/disc_mri/scan_11_3_2023_twins_nii_rot/'+outsvr):
            continue

        cmd = (
            "docker run --rm --mount type=bind,source=/deneb_disk/disc_mri/scan_11_3_2023_twins_nii_rot,target=/home/data fetalsvrtk/svrtk /bin/bash -c \"cd /home/data;ps;ls; mirtk reconstruct "
            + outsvr
            + " "
            + str(num_stacks)
            + str_stacks
            + " --resolution "
            + str(res) 
        )

        cmd += " --thickness" + str_th + " -template " + template + " --mask " + mask + "\""

        print(cmd)
        os.system(cmd)
