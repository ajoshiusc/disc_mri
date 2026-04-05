import SimpleITK as sitk

fixed_path = "/deneb_disk/disc_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA30.nii.gz"
fixed_image = sitk.ReadImage(fixed_path, sitk.sitkFloat32)
fixed_mask = sitk.Cast(fixed_image > 0, sitk.sitkUInt8)

ex_method = sitk.ImageRegistrationMethod()
try:
    ex_method.SetMetricFixedMask(fixed_mask)
    print("SetMetricFixedMask works!")
except Exception as e:
    print("Error:", e)

