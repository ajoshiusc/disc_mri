import nilearn.image as ni
import numpy as np
from scipy.ndimage import binary_fill_holes
import seaborn as sns
import matplotlib.pyplot as plt
from numpy import std, mean, sqrt
import glob
import os
import SimpleITK as sitk
import uuid

tissue_file = '/deneb_disk/3T_vs_low_field/3T_mprage_data_BrainSuite/subj2_vol1/T1.pvc.frac.nii.gz'


def load_imgT1(input_nii):

        # run N4 bias field correction
    inputImage = sitk.ReadImage(input_nii, sitk.sitkFloat32)
    nii_filename = str(uuid.uuid4())+'.nii.gz'

    maskImage = sitk.OtsuThreshold(inputImage, 0, 1, 200)
    sitk.WriteImage(maskImage, 'mask.nii.gz')

    corrector = sitk.N4BiasFieldCorrectionImageFilter()
    corrected_image = corrector.Execute(inputImage, maskImage)
    sitk.WriteImage(corrected_image, nii_filename)

    return(ni.load_img(nii_filename))

# correct if the population S.D. is expected to be equal for the two groups.
def cohen_d(x, y):
    nx = len(x)
    ny = len(y)
    dof = nx + ny - 2
    return (mean(x) - mean(y)) / sqrt(((nx-1)*std(x, ddof=1) ** 2 + (ny-1)*std(y, ddof=1) ** 2) / dof)




subdirs = glob.glob(
    '/deneb_disk/3T_vs_low_field/parameter_tuning/parameter_tuning_subj2_vo1_BrainSuite/*')

for subdir in subdirs:

    dir, param = os.path.split(subdir)

    img_file1 = '/deneb_disk/3T_vs_low_field/registered_data_param_tuning/T1' + \
        param + 'to_3T.nii.gz'

    img = load_imgT1(img_file1).get_fdata()
    # Convert to int16
    lab = ni.load_img(tissue_file).get_fdata()

    gm_ind = (lab > 1.6) & (lab < 2.4)
    gm_val = img[gm_ind]

    wm_ind = (lab > 2.6)
    wm_val = img[wm_ind]

    print(lab.shape)
    print(gm_val.shape)
    print(gm_ind)

    #plt.hist([gm_val,wm_val],color=['r','b'], bins=30,alpha=.5)
    s = sns.histplot(data=[gm_val, wm_val], color=[
                     'r', 'b'], bins=30, alpha=.5)
    plt.legend(labels=["GM image intensity", "WM image intensity"])

    #sns.histplot(data=wm_val, bins=30)


    d = cohen_d(wm_val, gm_val)
    gmstd = np.std(gm_val)
    wmstd = np.std(wm_val)
    
    s.set(title=f'param={param}, ' + f'Cohens d: {d:.2f}, GM std: {gmstd:.2f}, WM std: {wmstd:.2f}')
    #plt.show()

    s.figure.savefig(f'{param}.png')

    #plt.close()

    print(f'Cohens d: {d}, GM std: {gmstd}, WM std: {wmstd}')




# Do the same for 3T scan vol2


img_file1 = '/deneb_disk/3T_vs_low_field/registered_data/sub2_H2_to_H1.nii.gz'

img = load_imgT1(img_file1).get_fdata()
# Convert to int16
lab = ni.load_img(tissue_file).get_fdata()

gm_ind = (lab > 1.6) & (lab < 2.4)
gm_val = img[gm_ind]

wm_ind = (lab > 2.6)
wm_val = img[wm_ind]

print(lab.shape)
print(gm_val.shape)
print(gm_ind)

#plt.hist([gm_val,wm_val],color=['r','b'], bins=30,alpha=.5)
s = sns.histplot(data=[gm_val, wm_val], color=[
                    'r', 'b'], bins=30, alpha=.5)
plt.legend(labels=["GM image intensity", "WM image intensity"])

#sns.histplot(data=wm_val, bins=30)


d = cohen_d(wm_val, gm_val)
gmstd = np.std(gm_val)
wmstd = np.std(wm_val)

s.set(title='param=3T scan 2, ' + f'Cohens d: {d:.2f}, GM std: {gmstd:.2f}, WM std: {wmstd:.2f}')
plt.show()

s.figure.savefig('3Tscan2.png')

print(f'Cohens d: {d}, GM std: {gmstd}, WM std: {wmstd}')




