import numpy as np
import glob
from tqdm import tqdm
import SimpleITK as sitk
import xml.etree.ElementTree as ET
import pandas as pd
from nilearn.image import load_img
from pandas import read_csv
import os
import seaborn as sns

vent_roi_id = 4
lst_files = glob.glob(
    '/deneb_disk/feta_2022/feta_2.2/sub-*/anat/s*dseg.nii.gz')

meta_data = read_csv(
    '/deneb_disk/feta_2022/feta_2.2/participants.tsv', sep='\t', index_col=0)

vent_vols = np.zeros(len(lst_files))
healthy = np.zeros(len(lst_files),dtype=bool)
g_age = np.zeros(len(lst_files))

for i, fname in enumerate(lst_files):

    sub_id = os.path.basename(fname)[:7]
    healthy[i] = meta_data['Pathology'][sub_id][0] == 'N'
    g_age[i] = meta_data['Gestational age'][sub_id]
    v = load_img(fname)
    vox_vol = np.prod(v.header['pixdim'][1:4])

    vent_vols[i] = np.sum(v.get_fdata() == vent_roi_id)*vox_vol


helathy_vent_vols = vent_vols[healthy]
healthy_g_age = g_age[healthy]


print(helathy_vent_vols.shape)

print(vent_vols.shape)

data = {'GAge': np.round(healthy_g_age), 'VentVol': helathy_vent_vols}

#data = {'GAge': np.round(healthy_g_age/4.0)*4, 'VentVol': helathy_vent_vols}
data = pd.DataFrame(data)

sns.lineplot(
    data=data,
    x="GAge", y="VentVol", markers=True, dashes=False
).figure.savefig('income_f_age.png')

