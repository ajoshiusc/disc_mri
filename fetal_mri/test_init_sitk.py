import SimpleITK as sitk
import numpy as np

fixed_path = "/deneb_disk/disc_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA30.nii.gz"
moving_path = "/deneb_disk/disc_mri/scan_8_11_2023/outsvr/image0.nii.gz"

fixed = sitk.ReadImage(fixed_path, sitk.sitkFloat32)
moving = sitk.ReadImage(moving_path, sitk.sitkFloat32)
fixed_mask = sitk.Cast(fixed > 0, sitk.sitkUInt8)

# 1. Geometry
t_geom = sitk.CenteredTransformInitializer(fixed, moving, sitk.Euler3DTransform(), sitk.CenteredTransformInitializerFilter.GEOMETRY)
print("Geometry:", t_geom.GetTranslation())

# 2. Moments
t_mom = sitk.CenteredTransformInitializer(fixed, moving, sitk.Euler3DTransform(), sitk.CenteredTransformInitializerFilter.MOMENTS)
print("Moments:", t_mom.GetTranslation())

