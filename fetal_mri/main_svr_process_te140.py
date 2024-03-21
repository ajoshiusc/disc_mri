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
template = subdir + '/p19_t2_haste_cor_head_te140_p.nii.gz'
mask = subdir + '/p19_t2_haste_cor_head_te140_p.mask.nii.gz'
fetal_atlas = '/home/ajoshi/projects/disc_mri/fetal_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA33.nii.gz'
fetal_atlas_seg = '/home/ajoshi/projects/disc_mri/fetal_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA33_regional.nii.gz'
fetal_atlas_tissue = '/home/ajoshi/projects/disc_mri/fetal_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA33_tissue.nii.gz'
outsvr_dir = "/deneb_disk/fetal_scan_6_2_2023/outsvr"


# create outsvr directory if it does not exist
if not os.path.exists(outsvr_dir):
    os.makedirs(outsvr_dir)


stacks_all = glob.glob(subdir + "/*head*te140*p.nii.gz")

res = 1
th = 3
MAX_COMB = 20


for num_stacks in (3,6,9,12): #range(1, len(stacks_all) + 1):
    for ns in range(MAX_COMB):
        stacks = random_combination(stacks_all, num_stacks)

        if ns > MAX_COMB:
            continue

        str_stacks = ""
        str_th = ""

        for s in stacks:
            str_stacks += " " + s
            str_th += " " + str(th)

        outsvr = f"{outsvr_dir}/svr_te98_numstacks_{num_stacks}_iter_{ns}.nii.gz"

        cmd = (
            "mirtk reconstruct "
            + outsvr
            + " "
            + str(num_stacks)
            + str_stacks
            + " --resolution "
            + str(res)
        )

        cmd += " --thickness" + str_th + " --template " + template + " --mask " + mask

        print(cmd)
        #os.system(cmd)
        docker_cmd = f'docker run --rm --mount type=bind,source=/deneb_disk,target=/deneb_disk fetalsvrtk/svrtk /bin/bash -lic \'cd {subdir}; {cmd}\''
        print(docker_cmd)
        os.system(docker_cmd)

