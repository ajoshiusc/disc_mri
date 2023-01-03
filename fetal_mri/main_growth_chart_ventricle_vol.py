import numpy as np
import glob
from tqdm import tqdm
import SimpleITK as sitk
import xml.etree.ElementTree as ET
import pandas as pd
from nilearn.image import load_img
from pandas import read_csv
import os


lst_files = glob.glob('/deneb_disk/feta_2022/feta_2.2/sub-*/anat/s*dseg.nii.gz')

meta_data = read_csv('/deneb_disk/feta_2022/feta_2.2/participants.tsv',sep='\t',index_col=0)

vent_vols = np.zeros(len(lst_files))
healthy = np.zeros(len(lst_files))
g_age = np.zeros(len(lst_files))

for i, fname in enumerate(lst_files):

    sub_id = os.path.basename(fname)[:7]
    healthy[i] = meta_data['Pathology'][sub_id]
    g_age[i] = meta_data['Gestational age'][sub_id]
    v = load_img(fname) 
    vox_vol = np.prod(v.header['pixdim'][1:4])

    vent_vols[i] = np.sum(v.get_fdata() == vent_roi_id)*vox_vol





