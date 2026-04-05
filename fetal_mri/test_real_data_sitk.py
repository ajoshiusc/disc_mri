import SimpleITK as sitk
import copy

fixed_path = "/deneb_disk/disc_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA30.nii.gz"
moving_path = "/deneb_disk/disc_mri/scan_8_11_2023/outsvr/image0.nii.gz"

fixed = sitk.ReadImage(fixed_path, sitk.sitkFloat32)
moving = sitk.ReadImage(moving_path, sitk.sitkFloat32)
fixed_low = sitk.Shrink(fixed, [4, 4, 4])
moving_low = sitk.Shrink(moving, [4, 4, 4])

# 1. Initialize translation using full-res images geometry center
initial_transform = sitk.CenteredTransformInitializer(
    fixed, moving, sitk.Euler3DTransform(), sitk.CenteredTransformInitializerFilter.GEOMETRY
)

R_ex = sitk.ImageRegistrationMethod()
R_ex.SetMetricAsMattesMutualInformation(numberOfHistogramBins=32)
R_ex.SetOptimizerAsExhaustive([4, 4, 4, 0, 0, 0])
R_ex.SetOptimizerScales([3.14159/4, 3.14159/4, 3.14159/4, 1.0, 1.0, 1.0])
R_ex.SetInitialTransform(initial_transform, inPlace=True)
R_ex.Execute(fixed_low, moving_low)

print("Type after exhaust:", type(initial_transform))

R_gd = sitk.ImageRegistrationMethod()
R_gd.SetMetricAsMattesMutualInformation(numberOfHistogramBins=32)
R_gd.SetOptimizerAsGradientDescent(1.0, 10, 1e-6, 10)
R_gd.SetInitialTransform(initial_transform, inPlace=True)
R_gd.SetOptimizerScalesFromPhysicalShift()
R_gd.Execute(fixed_low, moving_low)

print("Type after GD:", type(initial_transform))

