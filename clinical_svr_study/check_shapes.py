import nibabel as nib
import os
folder = "/home/ajoshi/Desktop/clinical_svr_video_files/"
raw = nib.load(os.path.join(folder, "BRAIN_AXIAL_SSh_TSE_esp56_1601.nii.gz"))
svr = nib.load(os.path.join(folder, "RND_0002_SVR_aligned.nii.gz"))
print("Raw shape:", raw.shape, "Voxel size:", raw.header.get_zooms())
print("SVR shape:", svr.shape, "Voxel size:", svr.header.get_zooms())
