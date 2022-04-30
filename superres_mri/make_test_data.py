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
mode = 'train'

num_samp = 150000

patch_size = [256, 256]
X = list()
Y = list()

for sub1 in tqdm(range(num_samp)):


        im1 = np.random.rand(patch_size[0],patch_size[1])
        im2 = np.random.rand(patch_size[0],patch_size[1])
        im3 = np.random.rand(patch_size[0],patch_size[1])
        im4 = np.random.rand(patch_size[0],patch_size[1])
        im5 = np.random.rand(patch_size[0],patch_size[1])



        #im1 = gaussian_filter(im1,1)
        im1 = im1-np.min(im1)
        im1 = im1/np.max(im1)
        im1 = np.minimum(im1,.5)/.5

        im2 = gaussian_filter(im2,2)
        im2 = im2-np.min(im2)
        im2 = im2/np.max(im2)
        im2 = np.minimum(im2,.5)/.5

        
        im = np.maximum(im1,im2)

        im = im/np.max(im)

        im_orig = im.copy()

        imsize = im.shape
        im = block_reduce(im,block_size=(4,1))

        im = resize(im,imsize)

        '''plt.imshow(im,cmap='gray')
        plt.colorbar()
        plt.show()

        plt.imshow(im_orig,cmap='gray')
        plt.colorbar()
        plt.show()'''



        X.append(np.uint8(255.0*im/im.max()))
        Y.append(np.uint8(255.0*im_orig/im_orig.max()))


hf = h5py.File('sim_noise_150'+mode+'.h5', 'w')
hf.create_dataset('X', data=X)
hf.create_dataset('Y', data=Y)
hf.close()
