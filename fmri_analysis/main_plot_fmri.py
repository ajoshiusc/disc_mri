#||AUM||
#||Shree Ganeshaya Namaha||

import numpy as np
import matplotlib.pyplot as plt


step_sizes = np.array([1,2,3,4,5,6,7,8,9,10])*.72

a1 = np.load('corr_samples_step.npz')
a2 = np.load('corr_samples_step5_10.npz')


err1 = a1['err']
err2 = a2['err']
err = np.concatenate((err1,err2), axis=2)

win_lengths = a1['win_lengths']*.72
nboot = 20

fig, (ax1, ax2) = plt.subplots(nrows=2, figsize=(6,10))

ax1.imshow(np.mean(err,axis=1), cmap=plt.get_cmap('gray'), aspect='auto',extent=[step_sizes[0],step_sizes[-1],win_lengths[-1],win_lengths[0]],vmin=0,vmax=5000)
ax1.set_title('mean error')

ax2.imshow(np.std(err,axis=1), cmap=plt.get_cmap('gray'), aspect='auto',extent=[step_sizes[0],step_sizes[-1],win_lengths[-1],win_lengths[0]],vmin=0,vmax=500)
ax2.set_title('std dev of error')

plt.tight_layout()
plt.show()