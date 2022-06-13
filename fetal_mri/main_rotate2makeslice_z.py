#||AUM||
#||Shree Ganeshaya Namaha||


import nilearn.image as ni
from sklearn.feature_extraction import img_to_graph
import numpy as np
import os

subdir = '/home/ajoshi/masked_trufi'
sub_file = '18_t2_trufi_tra_head_rep1_mask.nii.gz'
sub_img = os.path.join(subdir,sub_file)
out_file = os.path.join(subdir,'p' + sub_file)


import SimpleITK as sitk

img = sitk.ReadImage(sub_img)
print (img.GetSpacing())

sliceaxis = np.argmax(img.GetSpacing())

if sliceaxis == 2:
    img2 = img

if sliceaxis == 1:
    img2 = sitk.PermuteAxes(img, [0,2,1])

if sliceaxis == 0:
    img2 = sitk.PermuteAxes(img, [2,1,0])


print (img2.GetSpacing())

sitk.WriteImage(img2, out_file)

