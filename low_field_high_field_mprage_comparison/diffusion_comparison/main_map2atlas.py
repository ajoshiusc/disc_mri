#AUM
#Shree Ganeshaya Namaha
import os


for subno in range(1,6):

    cmd = f"~/Software/BrainSuite23a/svreg/bin/svreg_apply_map.sh /deneb_disk/3T_vs_low_field/FA_MD_for_common_space/MPRAGE_BrainSuite_4bfc/V1_LF_mprage_vol1_recon_GNL/T1.svreg.inv.map.nii.gz /deneb_disk/3T_vs_low_field/FA_MD_for_common_space/MD/V1_LF_SER_MD_vol1_wm.nii.gz /deneb_disk/3T_vs_low_field/FA_MD_for_common_space/MD/V1_LF_SER_MD_vol1_wm.atlas.nii.gz /home/ajoshi/Software/BrainSuite23a/svreg/BrainSuiteAtlas1/mri.bfc.nii.gz"
    os.system(cmd)

    