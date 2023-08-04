import nilearn.image as ni
from sklearn.feature_extraction import img_to_graph
import numpy as np
import os
import SimpleITK as sitk
import glob


sublist = glob.glob('/deneb_disk/SVR_8_3_2023/nii_data/S*')

for subdir in sublist:

    subname = os.path.basename(subdir)

    outsubdir = '/deneb_disk/SVR_8_3_2023/svr_output/' + subname

    if not os.path.isdir(outsubdir):
        os.makedirs(outsubdir)

    sub_files = glob.glob(subdir+'/*BRAIN*TSE*.nii.gz')

    for s in sub_files:

        sub_file=os.path.basename(s)

        sub_img = os.path.join(subdir,sub_file)
        out_file = os.path.join(outsubdir,'p' + sub_file)


        img = sitk.ReadImage(sub_img)
        print (img.GetSpacing())

        sliceaxis = np.argmax(img.GetSpacing())

        if sliceaxis == 2:
            img2 = img

        if sliceaxis == 1:
            img2 = sitk.PermuteAxes(img, [0,2,1])

        if sliceaxis == 0:
            img2 = sitk.PermuteAxes(img, [2,1,0])


        print(img2.GetSpacing())

        sitk.WriteImage(img2, out_file)

