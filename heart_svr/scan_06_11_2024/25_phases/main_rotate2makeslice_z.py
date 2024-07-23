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
    all_scans = '/deneb_disk/disc_mri/for_Ye_7_18_2024/25_phase_data'

    for phase in range(25):
        scan_dir = all_scans + '/nifti_phase_' + f"{phase+1:02}"
        print(scan_dir)

        out_dir = scan_dir + '_rot'

        make_slices(scan_dir, out_dir)  # call the function


if __name__ == '__main__':
    main()

# End of main_rotate2makeslice_z.py