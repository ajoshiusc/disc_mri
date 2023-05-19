import nilearn.image as ni
import numpy as np
from scipy.ndimage import binary_fill_holes
import seaborn as sns
import matplotlib.pyplot as plt
from numpy import std, mean, sqrt
import numpy as np
import nibabel as nib
import matplotlib.pyplot as plt


te1='98'
te2 = '181'
te3 = '272'

img_file1 = '/deneb_disk/fetal_scan_8_3_2022/haste_head_te'+te1+'_rot/outsvr_reorient_bst.nii.gz'
tissue_file1 = '/deneb_disk/fetal_scan_8_3_2022/haste_head_te'+te1+'_rot/warped_tissue.nii.gz'
wm_tissue_file1 = '/deneb_disk/fetal_scan_8_3_2022/haste_head_te'+te1+'_rot/warped_labels.nii.gz'

img_file2 = '/deneb_disk/fetal_scan_8_3_2022/haste_head_te'+te2+'_rot/outsvr_reorient_bst.nii.gz'

img_file3 = '/deneb_disk/fetal_scan_8_3_2022/haste_head_te'+te3+'_rot/outsvr_reorient_bst.nii.gz'


# Load nifti images
img1 = nib.load(img_file1)
img2 = nib.load(img_file2)
img3 = nib.load(img_file3)

# Extract TE values from nifti header
TE = [98,181,272]

# Extract 3D image data
data1 = img1.get_fdata()
data2 = img2.get_fdata()
data3 = img3.get_fdata()


data = np.stack((data1,data2,data3),axis=3)


# Calculate T2 map
t2_map = np.zeros_like(data1)
for i in range(data.shape[0]):
    for j in range(data.shape[1]):
        for k in range(data.shape[2]):

            signal = data[i,j,k,:]
            t2_fit = np.polyfit(TE, np.log(signal), 1)
            t2_map[i,j,k] = -1/t2_fit[0]



# Display T2 map
plt.imshow(t2_map, cmap='gray')
plt.title('T2 map')
plt.colorbar()
plt.show()