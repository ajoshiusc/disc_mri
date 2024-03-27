import nibabel as nib
import numpy as np
import imageio

# Load the NIfTI image
nifti_file = "/deneb_disk/disc_mri/scan_8_11_2023/outsvr/svr_te140_numstacks_12_iter_0_aligned.nii.gz"  # Replace with your input NIfTI file
img = nib.load(nifti_file)
data = img.get_fdata()
data = 1.5 * 255.0 * data / np.max(data)

# Define the output GIF file
output_gif = "svr_te140_x.gif"

# Define the number of frames and the panning direction
num_frames = data.shape[0]  # 30
panning_direction = "x"  # 'z' for panning along the Z-axis

# Calculate the panning step size
if panning_direction == "x":
    panning_step = data.shape[0] // num_frames
else:
    raise ValueError("Invalid panning direction. Use 'x' for X-axis panning.")

# Create the panning movie frames
frames = []
for i in range(num_frames):
    if panning_direction == "x":
        frame = data[i * panning_step : (i + 1) * panning_step, :, :].squeeze()
        # frame = np.uint8(frame)
        frame = np.fliplr(np.rot90(frame, 1))  # Rotate the frame if necessary
        frames.append(frame)

# Save the frames as a GIF
imageio.mimsave(output_gif, frames, duration=0.2, loop=0)  # Adjust duration as needed
