import nilearn.image as ni
from sklearn.feature_extraction import img_to_graph
import numpy as np
import os
import SimpleITK as sitk
import glob
from monai.metrics.regression import SSIMMetric, MSEMetric
from nilearn.image import load_img
from monai.transforms import EnsureChannelFirst
from tqdm import tqdm
from monai.losses.ssim_loss import SSIMLoss
from torch.nn import MSELoss

import matplotlib.pyplot as plt

subdirs = glob.glob("/deneb_disk/SVR_8_3_2023/svr_output_manual_mask/S*012")

for subdir in subdirs:
    os.system("cd " + subdir)
    subname = os.path.basename(subdir)
    mask = glob.glob(subdir + "/*.mask.nii.gz")[0]
    template = mask[:-12] + ".nii.gz"
    outsvr = os.path.join(subdir, subname + "_SVR.nii.gz")
    stacks = glob.glob(subdir + "/p*1.nii.gz")

    res = 1

    # th = 3

    num_stacks = len(stacks)

    str_stacks = ""
    str_th = ""

    for s in stacks:
        str_stacks += " " + s

        img = sitk.ReadImage(s)
        print(img.GetSpacing())
        th = np.max(img.GetSpacing())

        str_th += " " + str(th)

    if not os.path.isfile(outsvr):
        cmd = (
            "cd "
            + subdir
            + ";"
            + "mirtksvr reconstruct "
            + outsvr
            + " "
            + str(num_stacks)
            + str_stacks
            + " --resolution "
            + str(res)
        )

        cmd += " --thickness" + str_th + " --template " + template + " --mask " + mask

        print(cmd)
        os.system(cmd)
