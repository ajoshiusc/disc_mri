import nilearn.image as ni
import glob
from tqdm import tqdm
from scipy.ndimage import zoom, gaussian_filter
import h5py
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

mode = 'train'

num_samp = 30000

patch_size = [256, 256]
X = list()
Y = list()


im1 = np.random.randn(patch_size[0],patch_size[1])
im2 = np.random.randn(patch_size[0],patch_size[1])
im3 = np.random.randn(patch_size[0],patch_size[1])
im4 = np.random.randn(patch_size[0],patch_size[1])
im5 = np.random.randn(patch_size[0],patch_size[1])



im1 = gaussian_filter(im1,1)
im2 = gaussian_filter(im2,2)*2
im3 = gaussian_filter(im3,3)*3
im4 = gaussian_filter(im4,4)*4
im5 = gaussian_filter(im5,5)*5



im = np.maximum(im1,im2)
im = np.maximum(im,im3)
im = np.maximum(im,im4)
im = np.maximum(im,im5)

im = im/np.max(im)

plt.imshow(im,cmap='gray')
plt.colorbar()

plt.show()



for sub1 in tqdm(range(num_samp)):

        X.append(np.uint8(255.0*slice/slice.max()))
        Y.append(np.uint8(labels))


hf = h5py.File('/deneb_disk/headreco_out/'+mode+'.h5', 'w')
hf.create_dataset('X', data=X)
hf.create_dataset('Y', data=Y)
hf.close()
