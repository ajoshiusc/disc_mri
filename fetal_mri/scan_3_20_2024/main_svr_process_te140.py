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


subdir = "/deneb_disk/disc_mri/scan_3_20_2024/nifti_rot"
template = subdir + "/p20_t2_haste_cor_head_te140_p.nii.gz"
mask = subdir + "/p20_t2_haste_cor_head_te140_p.mask.nii.gz"

stacks_all = glob.glob(subdir + "/*head*te140*p.nii.gz")

res = 1
th = 3
MAX_COMB = 20

outsvr = "/deneb_disk/disc_mri/scan_3_20_2024/outsvr"

for num_stacks in (3, 6, 9, 10):  # range(1, len(stacks_all) + 1):
    for ns in range(MAX_COMB):
        stacks = random_combination(stacks_all, num_stacks)

        if ns > MAX_COMB:
            continue

        str_stacks = ""
        str_th = ""

        for s in stacks:
            str_stacks += " " + s
            str_th += " " + str(th)

        outsvr = f"svr_te140_numstacks_{num_stacks}_iter_{ns}.nii.gz"

        if os.path.isfile("outsvr/" + outsvr):
            continue

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
        # os.system(cmd)
        docker_cmd = f"docker run --rm --mount type=bind,source=/deneb_disk,target=/deneb_disk fetalsvrtk/svrtk /bin/bash -lic 'cd {subdir}; {cmd}'"
        print(docker_cmd)
        os.system(docker_cmd)
