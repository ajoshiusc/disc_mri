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


subdir = "/deneb_disk/disc_mri/for_Ye_7_18_2024/nifti_rot"
template = subdir + "/p61_cardiac_multi_slice_real_time_spiral_ssfp_ga_res_22.nii.gz"
mask = subdir + "/p61_cardiac_multi_slice_real_time_spiral_ssfp_ga_res_22.mask.nii.gz"

stacks_all = glob.glob(subdir + "/*22.nii.gz")

res = 2
th = 8
MAX_COMB = 20

outsvr_dir = "/deneb_disk/disc_mri/for_Ye_7_18_2024/outsvr"

stacks = " " + stacks_all[0]

outsvr = f"svr_heart_2mm.nii.gz"

num_stacks = 1
res = 1.0
th=8.0
str_th=str(th)

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
