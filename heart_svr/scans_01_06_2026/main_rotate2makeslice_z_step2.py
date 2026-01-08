import nilearn.image as ni
from sklearn.feature_extraction import img_to_graph
import numpy as np
import os
import SimpleITK as sitk
import glob
from itertools import product

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

        sliceaxis = np.argmax(img.GetSpacing())

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
 
    # scans_dir = '/deneb_disk/fetal_scan_8_3_2022/data'
    scans_dir_top = ("/project2/ajoshi_27/data/heart_svr/nifti_files")
    expmt_dir_all = glob.glob(scans_dir_top + "/vol*")


    for phase, expmt_dir in product(range(25),expmt_dir_all):

        # stack_id =stack_dir.split('ssfp_')[-1][0:8]
        stack_dir_all = [expmt_dir] #glob.glob(expmt_dir + "/*")

        for stack_dir in stack_dir_all:

            inp_dir = expmt_dir + f'/phase_{phase+1:02d}'
            out_expmt_dir = "/project2/ajoshi_27/data/heart_svr/nifti_files/" + expmt_dir.split('/')[-1] 

            if not os.path.isdir(out_expmt_dir):
                os.mkdir(out_expmt_dir)
            
            out_stack_dir = out_expmt_dir #+ '/' + stack_dir.split('/')[-1]

            if not os.path.isdir(out_stack_dir):
                os.mkdir(out_stack_dir)

            out_dir = out_stack_dir + f'/phase_{phase+1:02d}_rot'

            if not os.path.isdir(out_dir):
                os.mkdir(out_dir)

            phase_dir = stack_dir + f'/phase_{phase+1:02d}'        


            make_slices(phase_dir, out_dir)  # call the function




if __name__ == '__main__':
    main()

# End of main_rotate2makeslice_z.py