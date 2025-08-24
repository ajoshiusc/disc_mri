import nilearn.image as ni
from sklearn.feature_extraction import img_to_graph
import numpy as np
import os
import SimpleITK as sitk
import glob
from itertools import product

def make_slices(subdir, outsubdir):
    if not os.path.isdir(outsubdir):
        os.makedirs(outsubdir)

    sub_files = glob.glob(subdir+'/*.nii.gz')

    for s in sub_files:
        sub_file = os.path.basename(s)
        sub_img = os.path.join(subdir, sub_file)
        out_file = os.path.join(outsubdir, 'p' + sub_file)

        img = sitk.ReadImage(sub_img)
        print(img.GetSpacing())

        sliceaxis = np.argmax(img.GetSpacing())

        if sliceaxis == 2:
            img2 = img

        elif sliceaxis == 1:
            img2 = sitk.PermuteAxes(img, [0, 2, 1])
            direction = np.array(img.GetDirection()).reshape(3, 3)
            new_direction = direction[:, [0, 2, 1]].flatten()
            img2.SetDirection(new_direction)
            img2.SetSpacing([img.GetSpacing()[0], img.GetSpacing()[2], img.GetSpacing()[1]])

        elif sliceaxis == 0:
            img2 = sitk.PermuteAxes(img, [2, 1, 0])
            direction = np.array(img.GetDirection()).reshape(3, 3)
            new_direction = direction[:, [2, 1, 0]].flatten()
            img2.SetDirection(new_direction)
            img2.SetSpacing([img.GetSpacing()[2], img.GetSpacing()[1], img.GetSpacing()[0]])

        img2.SetOrigin(img.GetOrigin())
        # Ensure the direction is set correctly
        img2.SetDirection(new_direction)

        
        print(img2.GetSpacing())
        print('-------------------')

        sitk.WriteImage(img2, out_file)

# write main function
def main():
    scans_dir_top = ("/deneb_disk/disc_mri/disc_mri/heart_svr_acquisition_03_03_2025/nifti_files")
    expmt_dir_all = glob.glob(scans_dir_top + "/vol1110*")

    for phase, expmt_dir in product(range(25), expmt_dir_all):
        stack_dir_all = [expmt_dir]

        for stack_dir in stack_dir_all:
            inp_dir = expmt_dir + f'/phase_{phase+1:02d}'
            out_expmt_dir = "/deneb_disk/disc_mri/disc_mri/heart_svr_acquisition_03_03_2025/nifti_files/" + expmt_dir.split('/')[-1]

            if not os.path.isdir(out_expmt_dir):
                os.mkdir(out_expmt_dir)

            out_stack_dir = out_expmt_dir

            if not os.path.isdir(out_stack_dir):
                os.mkdir(out_stack_dir)

            out_dir = out_stack_dir + f'/phase_{phase+1:02d}_rot'

            if not os.path.isdir(out_dir):
                os.mkdir(out_dir)

            phase_dir = stack_dir + f'/phase_{phase+1:02d}'

            make_slices(phase_dir, out_dir)

if __name__ == '__main__':
    main()