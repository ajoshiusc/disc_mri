#AUM#
#Shree Ganeshaya Namah

# Read T1 and T2 images, calculate T1/T2 ratio, and write the result to a new NIfTI file
import nibabel as nib
from nibabel.nifti1 import Nifti1Image
import numpy as np
import os

def calculate_t1_t2_ratio(t1_path, t2_path, mask_path, output_path):
    # Load T1 and T2 images
    t1_img = nib.load(t1_path)
    t2_img = nib.load(t2_path)
    mask_img = nib.load(mask_path)

    # Convert to numpy arrays
    t1_data = t1_img.get_fdata()
    t2_data = t2_img.get_fdata()    
    mask_data = mask_img.get_fdata()



# write main function to calculate T1/T2 ratio
    # Calculate T1/T2 ratio, avoiding division by zero
    with np.errstate(divide='ignore', invalid='ignore'):
        t1_t2_ratio = np.where(mask_data > 0, t1_data / t2_data, 0)

    t1_t2_ratio = t1_t2_ratio.astype(np.float32)
    t1_t2_ratio_img = nib.Nifti1Image(t1_t2_ratio, affine=t1_img.affine, header=t1_img.header)
    t1_t2_ratio_img.set_data_dtype(np.float32)

    # Save the T1/T2 ratio image
    nib.save(t1_t2_ratio_img, output_path)
    print(f"T1/T2 ratio saved to {output_path}")

if __name__ == "__main__":
    # Define file paths

    # list t1 files

    t1list = os.listdir('/home/ajoshi/Downloads/nihpd_obj2_asym_nifti/')
    t1list = [f for f in t1list if 't1w' in f and f.endswith('.nii')]
    print("T1 files found:", t1list)

    for t1 in t1list:
        # Construct corresponding T2 and mask paths

        t1_path = os.path.join('/home/ajoshi/Downloads/nihpd_obj2_asym_nifti/', t1)
        t2_path = t1_path.replace('t1w', 't2w')
        mask_path = t1_path.replace('t1w', 'mask')
        
        # Check if T2 and mask files exist
        if not os.path.exists(t2_path) or not os.path.exists(mask_path):
            print(f"Skipping {t1_path}: corresponding T2 or mask file not found.")
            continue
        
        # Define output path
        output_path = t1_path.replace('t1w', 't1_t2_ratio').replace('.nii', '.nii.gz')

        # Calculate T1/T2 ratio
        calculate_t1_t2_ratio(t1_path, t2_path, mask_path, output_path)

    '''
    t1_path = '/home/ajoshi/Downloads/nihpd_obj2_asym_nifti/nihpd_asym_44-60_t1w.nii'
    t2_path = '/home/ajoshi/Downloads/nihpd_obj2_asym_nifti/nihpd_asym_44-60_t2w.nii'
    mask_path = '/home/ajoshi/Downloads/nihpd_obj2_asym_nifti/nihpd_asym_44-60_mask.nii'
    output_path = '/home/ajoshi/Downloads/nihpd_obj2_asym_nifti/nihpd_asym_44-60_t1_t2_ratio.nii.gz'

    # Calculate T1/T2 ratio
    calculate_t1_t2_ratio(t1_path, t2_path, mask_path, output_path)
    '''