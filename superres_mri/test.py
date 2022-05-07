import argparse
import logging
import os
import random
import sys
import numpy as np
import torch
import torch.backends.cudnn as cudnn
import torch.nn as nn
from torch.utils.data import DataLoader
from tqdm import tqdm
from utils import test_single_nii
from networks.vit_seg_modeling import VisionTransformer as ViT_seg
from networks.vit_seg_modeling import CONFIGS as CONFIGS_ViT_seg
import SimpleITK as sitk

parser = argparse.ArgumentParser()
'''parser.add_argument('--volume_path', type=str,
                    default='../data/Synapse/test_vol_h5', help='root dir for validation volume data')  # for acdc volume_path=root_dir
parser.add_argument('--dataset', type=str,
                    default='SuperRes', help='experiment_name')
parser.add_argument('--num_classes', type=int,
                    default=1, help='output channel of network')

parser.add_argument('--max_iterations', type=int,default=20000, help='maximum epoch number to train')
parser.add_argument('--max_epochs', type=int, default=30, help='maximum epoch number to train')
parser.add_argument('--batch_size', type=int, default=24,
                    help='batch_size per gpu')
parser.add_argument('--img_size', type=int, default=256, help='input patch size of network input')
parser.add_argument('--is_savenii', action="store_true", help='whether to save results during inference')

parser.add_argument('--n_skip', type=int, default=3, help='using number of skip-connect, default is num')'''
parser.add_argument('--vit_name', type=str, default='R50-ViT-B_16', help='select one vit model')

'''parser.add_argument('--test_save_dir', type=str, default='../predictions', help='saving prediction as nii!')
parser.add_argument('--deterministic', type=int,  default=1, help='whether use deterministic training')
parser.add_argument('--base_lr', type=float,  default=0.01, help='segmentation network learning rate')
parser.add_argument('--seed', type=int, default=1234, help='random seed')
parser.add_argument('--vit_patches_size', type=int, default=16, help='vit_patches_size, default is 16')'''
args = parser.parse_args()

def inference(args, model, output_fname='out.nii.gz'):
    model.eval()

    # run N4 bias field correction
    inputImage = sitk.ReadImage(args.volume_path, sitk.sitkFloat32)
    image = inputImage
    maskImage = sitk.OtsuThreshold(inputImage, 0, 1, 200)
    corrector = sitk.N4BiasFieldCorrectionImageFilter()
    numberFittingLevels = 4
    corrected_image = image #corrector.Execute(image, maskImage)
    #log_bias_field = corrector.GetLogBiasFieldAsImage(inputImage)
    #corrected_image_full_resolution = inputImage / sitk.Exp( log_bias_field )
    sitk.WriteImage(corrected_image, 'input.bfc.nii.gz')

    test_single_nii('input.bfc.nii.gz', net, patch_size=[256, 256], output_fname=output_fname)



if __name__ == "__main__":

    cudnn.benchmark = False
    cudnn.deterministic = True
    random.seed(1234)
    np.random.seed(1234)
    torch.manual_seed(1234)
    img_size = 256
    vit_patches_size=16



    config_vit = CONFIGS_ViT_seg[args.vit_name]
    config_vit.n_classes = 1 #args.num_classes
    config_vit.n_skip = 3 #args.n_skip
    config_vit.patches.size = (16, 16)
    if args.vit_name.find('R50') !=-1:
        config_vit.patches.grid = (int(img_size/vit_patches_size), int(img_size/vit_patches_size))
    net = ViT_seg(config_vit, img_size=img_size, num_classes=1)#.cuda()

    snapshot = '/project/ajoshi_27/code_farm/disc_mri/superres_mri/model/TU_SuperRes256/TU_R50-ViT-B_16_skip3_epo150_bs4_256/epoch_36.pth'
    if not os.path.exists(snapshot): snapshot = snapshot.replace('best_model', 'epoch_'+str(args.max_epochs-1))
    net.load_state_dict(torch.load(snapshot,map_location=torch.device('cpu')))

    args.volume_path = 'BCI256.nii.gz'
    inference(args, net, output_fname='out.nii.gz')


