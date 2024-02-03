# AUM
# Shree Ganeshaya Namaha
import os
from itertools import product

for subno, vol in product(range(1, 6), range(1, 3)):
    # Warp MD to atlas
    cmd = f"/home/ajoshi/Software/BrainSuite23a/svreg_23a_build2505_linux/bin/svreg_apply_map.sh /deneb_disk/3T_vs_low_field/3T_mprage_data_BrainSuite_4bfc/subj{subno}_vol1/T1.svreg.inv.map.nii.gz /deneb_disk/3T_vs_low_field/FA_MD_for_common_space/FA_MD_in_3T_coordinate/MD/V{subno}_LF_SER_MD_vol{vol}_T1_GNL_aligned_3T.nii.gz /deneb_disk/3T_vs_low_field/FA_MD_for_common_space/FA_MD_in_3T_coordinate/MD_warped/V{subno}_LF_SER_MD_vol{vol}_T1_GNL_aligned_3T.atlas.nii.gz /home/ajoshi/Software/BrainSuite23a/svreg/BrainSuiteAtlas1/mri.bfc.nii.gz 0"
    print(cmd)
    os.system(cmd)

    cmd = f"/home/ajoshi/Software/BrainSuite23a/svreg_23a_build2505_linux/bin/svreg_apply_map.sh /deneb_disk/3T_vs_low_field/3T_mprage_data_BrainSuite_4bfc/subj{subno}_vol1/T1.svreg.inv.map.nii.gz /deneb_disk/3T_vs_low_field/FA_MD_for_common_space/FA_MD_in_3T_coordinate/MD/V{subno}_LF_SENSE_MD_vol{vol}_T1_GNL_aligned_3T.nii.gz /deneb_disk/3T_vs_low_field/FA_MD_for_common_space/FA_MD_in_3T_coordinate/MD_warped/V{subno}_LF_SENSE_MD_vol{vol}_T1_GNL_aligned_3T.atlas.nii.gz /home/ajoshi/Software/BrainSuite23a/svreg/BrainSuiteAtlas1/mri.bfc.nii.gz 0"
    print(cmd)
    os.system(cmd)

    cmd = f"/home/ajoshi/Software/BrainSuite23a/svreg_23a_build2505_linux/bin/svreg_apply_map.sh /deneb_disk/3T_vs_low_field/3T_mprage_data_BrainSuite_4bfc/subj{subno}_vol1/T1.svreg.inv.map.nii.gz /deneb_disk/3T_vs_low_field/FA_MD_for_common_space/FA_MD_in_3T_coordinate/MD/V{subno}_3T_SENSE_MD_vol{vol}_T1_GNL.nii.gz /deneb_disk/3T_vs_low_field/FA_MD_for_common_space/FA_MD_in_3T_coordinate/MD_warped/V{subno}_3T_SENSE_MD_vol{vol}_T1_GNL.atlas.nii.gz /home/ajoshi/Software/BrainSuite23a/svreg/BrainSuiteAtlas1/mri.bfc.nii.gz 0"
    print(cmd)
    os.system(cmd)



    # Warp FA to atlas
    cmd = f"/home/ajoshi/Software/BrainSuite23a/svreg_23a_build2505_linux/bin/svreg_apply_map.sh /deneb_disk/3T_vs_low_field/3T_mprage_data_BrainSuite_4bfc/subj{subno}_vol1/T1.svreg.inv.map.nii.gz /deneb_disk/3T_vs_low_field/FA_MD_for_common_space/FA_MD_in_3T_coordinate/FA/V{subno}_LF_SER_FA_vol{vol}_T1_GNL_aligned_3T.nii.gz /deneb_disk/3T_vs_low_field/FA_MD_for_common_space/FA_MD_in_3T_coordinate/FA_warped/V{subno}_LF_SER_FA_vol{vol}_T1_GNL_aligned_3T.atlas.nii.gz /home/ajoshi/Software/BrainSuite23a/svreg/BrainSuiteAtlas1/mri.bfc.nii.gz 0"
    print(cmd)
    os.system(cmd)

    cmd = f"/home/ajoshi/Software/BrainSuite23a/svreg_23a_build2505_linux/bin/svreg_apply_map.sh /deneb_disk/3T_vs_low_field/3T_mprage_data_BrainSuite_4bfc/subj{subno}_vol1/T1.svreg.inv.map.nii.gz /deneb_disk/3T_vs_low_field/FA_MD_for_common_space/FA_MD_in_3T_coordinate/FA/V{subno}_LF_SENSE_FA_vol{vol}_T1_GNL_aligned_3T.nii.gz /deneb_disk/3T_vs_low_field/FA_MD_for_common_space/FA_MD_in_3T_coordinate/FA_warped/V{subno}_LF_SENSE_FA_vol{vol}_T1_GNL_aligned_3T.atlas.nii.gz /home/ajoshi/Software/BrainSuite23a/svreg/BrainSuiteAtlas1/mri.bfc.nii.gz 0"
    print(cmd)
    os.system(cmd)

    cmd = f"/home/ajoshi/Software/BrainSuite23a/svreg_23a_build2505_linux/bin/svreg_apply_map.sh /deneb_disk/3T_vs_low_field/3T_mprage_data_BrainSuite_4bfc/subj{subno}_vol1/T1.svreg.inv.map.nii.gz /deneb_disk/3T_vs_low_field/FA_MD_for_common_space/FA_MD_in_3T_coordinate/FA/V{subno}_3T_SENSE_FA_vol{vol}_T1_GNL.nii.gz /deneb_disk/3T_vs_low_field/FA_MD_for_common_space/FA_MD_in_3T_coordinate/FA_warped/V{subno}_3T_SENSE_FA_vol{vol}_T1_GNL.atlas.nii.gz /home/ajoshi/Software/BrainSuite23a/svreg/BrainSuiteAtlas1/mri.bfc.nii.gz 0"
    print(cmd)
    os.system(cmd)


    