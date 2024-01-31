# AUM
# Shree Ganeshaya Namaha
import os
from itertools import product

for subno, vol in product(range(1, 6), range(1, 3)):
    # Warp MD to atlas
    cmd = f"/home/ajoshi/Software/BrainSuite23a/svreg_23a_build2505_linux/bin/svreg_apply_map.sh /deneb_disk/3T_vs_low_field/FA_MD_for_common_space/MPRAGE_BrainSuite_4bfc/V{subno}_LF_mprage_vol1_recon_GNL/T1.svreg.inv.map.nii.gz /deneb_disk/3T_vs_low_field/FA_MD_for_common_space/new_FA_MD/MD/V{subno}_LF_SER_MD_vol{vol}_T1_GNL.nii.gz /deneb_disk/3T_vs_low_field/FA_MD_for_common_space/new_FA_MD/MD_warped/V{subno}_LF_SER_MD_vol{vol}_T1_GNL.atlas.nii.gz /home/ajoshi/Software/BrainSuite23a/svreg/BrainSuiteAtlas1/mri.bfc.nii.gz 0"
    print(cmd)
    os.system(cmd)

    # Warp FA to atlas
    cmd = f"/home/ajoshi/Software/BrainSuite23a/svreg_23a_build2505_linux/bin/svreg_apply_map.sh /deneb_disk/3T_vs_low_field/FA_MD_for_common_space/MPRAGE_BrainSuite_4bfc/V{subno}_LF_mprage_vol1_recon_GNL/T1.svreg.inv.map.nii.gz /deneb_disk/3T_vs_low_field/FA_MD_for_common_space/new_FA_MD/FA/V{subno}_LF_SER_FA_vol{vol}_T1_GNL.nii.gz /deneb_disk/3T_vs_low_field/FA_MD_for_common_space/new_FA_MD/FA_warped/V{subno}_LF_SER_FA_vol{vol}_T1_GNL.atlas.nii.gz /home/ajoshi/Software/BrainSuite23a/svreg/BrainSuiteAtlas1/mri.bfc.nii.gz 0"
    print(cmd)
    os.system(cmd)
