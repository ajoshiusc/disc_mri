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
VERBOSE = False

mode = 'train'

num_samp = int(300000)

patch_size = [256, 256]
X = list()
Y = list()

for sub1 in tqdm(range(num_samp)):

    im1 = np.random.rand(patch_size[0], patch_size[1])
    im2 = np.random.rand(patch_size[0], patch_size[1])
    '''    im3 = np.random.rand(patch_size[0],patch_size[1])
        im4 = np.random.rand(patch_size[0],patch_size[1])
        im5 = np.random.rand(patch_size[0],patch_size[1])'''

    im2 = gaussian_filter(im2, 10*np.random.rand(2))
    im2 = np.random.rand(1)*(im2 > 0.5)
    #im1 = im1-np.min(im1)
    #im1 = im1/np.max(im1)
    #im1 = np.minimum(im1,.5)/.5

    #im2 = gaussian_filter(im2,2)
    #im2 = im2-np.min(im2)
    #im2 = im2/np.max(im2)
    #im2 = np.minimum(im2,.5)/.5

    #im = np.maximum(im1,im2)

    im = im1

    #im = im/np.max(im)

    im_orig = im.copy()

    imsize = im.shape
    im = block_reduce(im, block_size=(2, 1), func=np.mean)

    im = resize(im, imsize)

    if VERBOSE:
        fig2, (ax2, ax3) = plt.subplots(nrows=1, ncols=2)  # two axes on figure

        fim1 = ax2.imshow(im, cmap='gray')
        plt.colorbar(fim1, ax=ax2)
        # plt.show()

        fim2 = ax3.imshow(im_orig, cmap='gray')
        plt.colorbar(fim2, ax=ax3)
        plt.show()

    X.append(np.uint8(255.0*im))
    Y.append(np.uint8(255.0*im_orig))


hf = h5py.File('pure_noise_ds2'+mode+'.h5', 'w')
hf.create_dataset('X', data=X)
hf.create_dataset('Y', data=Y)
hf.close()
