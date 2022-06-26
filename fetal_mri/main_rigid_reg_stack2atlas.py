
import SimpleITK as sitk

import numpy as np
import os


input_dir = '/home/ajoshi/mydocker/fetal_scan_maria_demo/fetal_mri_datasets/motion_corrupted_sstse_brain_phantom_stacks/stacks/'

atlas_img = '/home/ajoshi/mydocker/fetal_scan_maria_demo/fetal_mri_datasets/motion_corrupted_sstse_brain_phantom_stacks/stacks/simulated-stack-d2.nii.gz'

#atlas_img = '/home/ajoshi/projects/disc_mri/fetal_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA32.nii.gz'
sub_vol = 'simulated-stack-d1.nii.gz'

sub_img = os.path.join(input_dir,sub_vol)

#atlas_img = sub_img

out_sub_img = os.path.join(input_dir,'atlas_'+sub_vol)

fixed_image =  sitk.ReadImage(atlas_img, sitk.sitkFloat32)
moving_image = sitk.ReadImage(sub_img, sitk.sitkFloat32)


initial_transform = sitk.CenteredTransformInitializer(fixed_image, 
                                                      moving_image, 
                                                      sitk.Euler3DTransform(), 
                                                      sitk.CenteredTransformInitializerFilter.GEOMETRY)

print(initial_transform)
registration_method = sitk.ImageRegistrationMethod()

# Similarity metric settings.
registration_method.SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)
registration_method.SetMetricSamplingStrategy(registration_method.RANDOM)
registration_method.SetMetricSamplingPercentage(1)

registration_method.SetInterpolator(sitk.sitkNearestNeighbor)

# Optimizer settings.
registration_method.SetOptimizerAsGradientDescent(learningRate=1, numberOfIterations=1000, convergenceMinimumValue=1e-6, convergenceWindowSize=10)
#registration_method.SetOptimizerScalesFromPhysicalShift()

# Setup for the multi-resolution framework.            
#registration_method.SetShrinkFactorsPerLevel(shrinkFactors = [4,2,1])
#registration_method.SetSmoothingSigmasPerLevel(smoothingSigmas=[2,1,0])
#registration_method.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()


# angle_z = -pi, 0, pi
registration_method.SetOptimizerAsExhaustive(numberOfSteps=[0,0,0,3,3,3], stepLength = 5*np.pi)
registration_method.SetOptimizerScales([1,1,1,1,1,1])


# Don't optimize in-place, we would possibly like to run this cell multiple times.
registration_method.SetInitialTransform(initial_transform, inPlace=False)

# Connect all of the observers so that we can perform plotting during registration.
#registration_method.AddCommand(sitk.sitkStartEvent, rgui.start_plot)
#registration_method.AddCommand(sitk.sitkEndEvent, rgui.end_plot)
#registration_method.AddCommand(sitk.sitkMultiResolutionIterationEvent, rgui.update_multires_iterations) 
#registration_method.AddCommand(sitk.sitkIterationEvent, lambda: rgui.plot_values(registration_method))

print('Initial metric value: {0}'.format(registration_method.GetMetricValue()))

final_transform = registration_method.Execute(fixed_image, moving_image)

print(final_transform)

# Always check the reason optimization terminated.
print('Final metric value: {0}'.format(registration_method.GetMetricValue()))
print('Optimizer\'s stopping condition, {0}'.format(registration_method.GetOptimizerStopConditionDescription()))

moving_resampled = sitk.Resample(moving_image, fixed_image, final_transform, sitk.sitkNearestNeighbor, 0.0, moving_image.GetPixelID())
sitk.WriteImage(moving_resampled, out_sub_img)
