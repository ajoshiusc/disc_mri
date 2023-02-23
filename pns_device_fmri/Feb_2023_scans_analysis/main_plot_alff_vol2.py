
import nilearn.image as ni
import os
from nilearn.plotting import plot_stat_map
from glob import glob

anat = '/deneb_disk/PNS_fMRI/PNS_fMRI/PNS_FMRI_20230215/bfpout/vol562/anat/vol562_T1w.bfc.nii.gz'

flist = glob('/deneb_disk/PNS_fMRI/PNS_fMRI/PNS_FMRI_20230215/bfpout/vol562/func/tmp/*')

for f in flist:

    alffz = os.path.basename(f)

    p = plot_stat_map(f,anat,threshold=1,cut_coords=[-9.366537,-25.68358,50.13907],vmax=4,draw_cross=False)

    p.savefig(alffz[:-7] + '.png')


