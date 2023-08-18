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


subdir = "/deneb_disk/fetal_data_8_11_2023/nifti_data_rot"
template = subdir + "/p10_t2_haste_tra_head_te140_p.nii.gz"
mask = subdir + "/p10_t2_haste_tra_head_te140_p.mask.nii.gz"

stacks_all = glob.glob(subdir + "/*head*te98*p.nii.gz")

res = 1
th = 3
MAX_COMB = 20


for num_stacks in range(1, len(stacks_all) + 1):
    for ns in range(MAX_COMB):
        stacks = random_combination(stacks_all, num_stacks)

        if ns > MAX_COMB:
            continue

        str_stacks = ""
        str_th = ""

        for s in stacks:
            str_stacks += " " + s
            str_th += " " + str(th)

        outsvr = f"outsvr/svr_te98_numstacks_{num_stacks}_iter_{ns}.nii.gz"

        cmd = (
            "cd outsvr; mirtk reconstruct "
            + outsvr
            + " "
            + str(num_stacks)
            + str_stacks
            + " --resolution "
            + str(res)
        )

        cmd += " --thickness" + str_th + " --template " + template + " --mask " + mask

        print(cmd)
        os.system(cmd)
