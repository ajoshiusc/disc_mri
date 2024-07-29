import nilearn.image as ni
from sklearn.feature_extraction import img_to_graph
import numpy as np
import os
import SimpleITK as sitk
import glob


# make the following code into a function
def make_slices(subdir, outsubdir):
    if not os.path.isdir(outsubdir):
        os.makedirs(outsubdir)

    sub_files = glob.glob(subdir+'/*.nii.gz')

    for s in sub_files:

        sub_file=os.path.basename(s)

        sub_img = os.path.join(subdir,sub_file)
        out_file = os.path.join(outsubdir,'p' + sub_file)


        img = sitk.ReadImage(sub_img)
        print (img.GetSpacing())

        sliceaxis = np.argmin(img.GetSpacing())

        if sliceaxis == 2:
            img2 = img

        if sliceaxis == 1:
            img2 = sitk.PermuteAxes(img, [0,2,1])

        if sliceaxis == 0:
            img2 = sitk.PermuteAxes(img, [2,1,0])


        print(img2.GetSpacing())

        sitk.WriteImage(img2, out_file)


# write main function
def main():
    all_scans = '/deneb_disk/disc_mri/for_Ye_Heart_07_26_2024/nifti_files'

    for phase in range(25):
        scans_dir = all_scans + '/phase_' + f"{phase+1:02}"
        print(scans_dir)

        out_dir = scans_dir + '_rot'

        make_slices(scans_dir, out_dir)  # call the function




if __name__ == '__main__':
    main()

# End of main_rotate2makeslice_z.py