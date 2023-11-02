import nibabel as nib
import numpy as np
import imageio

# Load the NIfTI image
nifti_file = '/deneb_disk/disc_mri/scan_8_11_2023/concat_z.nii.gz'  # Replace with your input NIfTI file
img = nib.load(nifti_file)
data = img.get_fdata()
data=1.5*255.0*data/np.max(data)

# Define the output GIF file
output_gif = 'panning_movie_z.gif'

# Define the number of frames and the panning direction
num_frames =  data.shape[2] #30
panning_direction = 'z'  # 'z' for panning along the Z-axis

# Calculate the panning step size
if panning_direction == 'z':
    panning_step = data.shape[2] // num_frames
else:
    raise ValueError("Invalid panning direction. Use 'z' for Z-axis panning.")

# Create the panning movie frames
frames = []
for i in range(num_frames):
    if panning_direction == 'z':
        frame = data[:, :, i * panning_step:(i + 1) * panning_step].squeeze()
        #frame = np.uint8(frame)
        frame = np.fliplr(np.rot90(frame,-1))  # Rotate the frame if necessary
        frames.append(frame)

# Save the frames as a GIF
imageio.mimsave(output_gif, frames, duration=0.2,loop=0)  # Adjust duration as needed
