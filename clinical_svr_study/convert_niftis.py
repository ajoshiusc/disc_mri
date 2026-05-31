import sys
import glob
import os
sys.path.append(os.path.abspath('nii2dcm'))
from main_clinical_svr_convert2dicom import run_nii2dcm

folder = "/home/ajoshi/Desktop/clinical_svr_video_files/"
nifti_files = glob.glob(os.path.join(folder, "*.nii.gz"))

for nii_file in nifti_files:
    sub = os.path.basename(nii_file).replace('.nii.gz', '')
    output_dcm_path = os.path.join(folder, f"{sub}_DICOM")
    os.makedirs(output_dcm_path, exist_ok=True)
    print(f"Converting {nii_file} to {output_dcm_path}")
    run_nii2dcm(nii_file, output_dcm_path, dicom_type='SVR', patient_name=sub)
print("Done")
