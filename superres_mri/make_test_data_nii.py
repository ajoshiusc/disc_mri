import nilearn.image as ni
import glob
from tqdm import tqdm
from scipy.ndimage import zoom, gaussian_filter
import h5py
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from skimage.measure import block_reduce
from skimage.transform import resize


nii_fname = 'BCI256.nii.gz'

image = ni.load_img(nii_fname).get_fdata()

image_ds = np.zeros_like(image)

for ind in tqdm(range(image.shape[2])):
    slice = image[:, :, ind]
    slice = 255.0*slice/(np.max(image) + 1e-3)

    image_ds[:, :, ind] = resize(block_reduce(
        slice, block_size=(2, 1), func=np.mean), slice.shape)


nii = ni.new_img_like(nii_fname, image_ds)

nii.to_filename('BCI256_ds2.nii.gz')
