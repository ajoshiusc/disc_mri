import nilearn.image as ni
import numpy as np
import os
import glob
from shutil import copyfile

out_dir = '/home/ajoshi/projects/disc_mri/clinical_svr_study/svr_8_3_2023/svr_aligned_randomized'
in_files=glob.glob('/home/ajoshi/projects/disc_mri/clinical_svr_study/svr_8_3_2023/svr_aligned_final/*.nii.gz')

p=10+np.array((17, 8, 2, 16, 11, 3, 7, 15, 10, 20, 4, 18, 5, 14, 9, 1, 19, 6, 12, 13))

print(p)



with open("output.txt", "a") as f:


    for f in in_files:
        sub_num = int(f[84:87])
        new_sub_num=p[sub_num-11]
        print(sub_num, f)
        new_f = os.path.join(out_dir,f'RND_{4%new_sub_num}_SVR_aligned.nii.gz')

        path, fname = os.path.split(f)

        copyfile(f, new_f)

        print(f'copying {f} \n to {new_f}\n',file=f)


        

