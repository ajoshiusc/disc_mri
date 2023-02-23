
import nilearn.image as ni
import os
from nilearn.plotting import plot_stat_map
from glob import glob

anat = '/deneb_disk/PNS_fMRI/PNS_fMRI/PNS_FMRI_20230215/bfpout/vol561/anat/vol561_T1w.bfc.nii.gz'

flist = glob('/deneb_disk/PNS_fMRI/PNS_fMRI/PNS_FMRI_20230215/bfpout/vol561/func/tmp/*')

for f in flist:

    alffz = os.path.basename(f)

    p = plot_stat_map(f,anat,threshold=1,cut_coords=[-0.3070512,-21.96586,60.31953],vmax=4,draw_cross=False)

    p.savefig(alffz[:-7] + '.png')


