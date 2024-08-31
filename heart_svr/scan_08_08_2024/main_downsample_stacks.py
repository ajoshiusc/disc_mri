# code for downsampling stacks

import nibabel as nib
import numpy as np
import glob
import os


def downsample_nifti(input_file, output_file, n):
    """
    Downsamples a NIfTI file by skipping every nth slide along the z direction.

    Args:
      input_file: Path to the input NIfTI file.
      output_file: Path to the output NIfTI file.
      n: The factor to downsample by.
    """

    # Load the NIfTI image
    img = nib.load(input_file)
    data = img.get_fdata()

    # Get image dimensions
    z_dim = data.shape[2]

    # Downsample along the z-axis
    data_downsampled = data[:, :, ::n]

    # modify the affine matrix and voxel spacing
    new_affine = img.affine.copy()
    #new_affine[2, 2] *= n
    
    # set zooms
    img.header.set_zooms((img.header.get_zooms()[0], img.header.get_zooms()[1], img.header.get_zooms()[2] * n))
    
    # Create a new NIfTI image with the downsampled data and updated header
    # Save the downsampled image make sure that the data type of the output image is the same as the input image
    data_downsampled = np.asanyarray(data_downsampled, dtype=img.get_data_dtype())
    img_downsampled = nib.Nifti1Image(data_downsampled, new_affine, img.header)

    # Save the downsampled image make sure that the data type of the output image is the same as the input image
    #img_downsampled.set_data_dtype(img.get_data_dtype())
    nib.save(img_downsampled, output_file)


downsample_factor = 2


input_phase_dir = (
    "/project/ajoshi_27/disc_mri/heart_svr_acquisition_08_08_2024/nifti_files/res_1.5_thickness_6/phase_11_rot"
)


# Get a list of all NIfTI files in the input directory
nii_files = glob.glob(input_phase_dir + "/*.nii.gz")


# Loop through each NIfTI file
for downsample_factor in [2]:

    output_phase_dir = f"/project/ajoshi_27/disc_mri/heart_svr_acquisition_08_08_2024/nifti_files_experiments/res_1.5_thickness_6/phase_11_rot_downsampled{downsample_factor}"
    print(output_phase_dir)
    # make output directory if it doesn't exist
    os.makedirs(output_phase_dir, exist_ok=True)

    for input_file in nii_files:
        
        # get filename
        filename = os.path.basename(input_file)
        print(f"Downsampling {filename}...")  # Let us know which file is being processed

        # create output file path
        output_file = os.path.join(output_phase_dir, filename.replace(".nii.gz", f"_downsampled{downsample_factor}.nii.gz"))


        # Downsample the NIfTI file
        downsample_nifti(input_file, output_file, downsample_factor)

print("Done!")  # Let us know it's done

# end of code
