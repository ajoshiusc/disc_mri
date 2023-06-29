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


subdir = '/deneb_disk/fetal_scan_6_2_2023/VOL632_nii_rot'
template = subdir + '/p43_t2_haste_tra_head_te181_p.nii.gz'
mask = subdir + '/p43_t2_haste_tra_head_te181_p.mask.nii.gz'
fetal_atlas = '/home/ajoshi/projects/disc_mri/fetal_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA33.nii.gz'
fetal_atlas_seg = '/home/ajoshi/projects/disc_mri/fetal_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA33_regional.nii.gz'
fetal_atlas_tissue = '/home/ajoshi/projects/disc_mri/fetal_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA33_tissue.nii.gz'


stacks_all = glob.glob(subdir + "/*head*te181*p.nii.gz")

res = 1
th = 3
MAX_COMB = 1


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

        outsvr = f"outsvr/svr_te181_numstacks_{num_stacks}_iter_{ns}.nii.gz"

        cmd = (
            "mirtksvr reconstruct "
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
