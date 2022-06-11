#||AUM||
#||Shree Ganeshaya Namaha||

import dicom2nifti
import glob
import os

scans_dir = '/ImagePTE1/ajoshi/data/fetal_scan_june_8_2022/Vol368_Fetal/Pediatric_Fetal - 1/'


scans = glob.glob(scans_dir+"/*")
out_dir = '/home/ajoshi/fetal_scan_6_8_2022'


for s in scans:
    print(s)

    dicom2nifti.convert_dir.convert_directory(s, out_dir, compression=True)













