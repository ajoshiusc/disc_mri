import SimpleITK as sitk
import numpy as np
import time

def test_exhaustive():
    fixed = sitk.Image([32, 32, 32], sitk.sitkFloat32)
    moving = sitk.Image([32, 32, 32], sitk.sitkFloat32)
    
    tx = sitk.Euler3DTransform()
    
    R = sitk.ImageRegistrationMethod()
    R.SetMetricAsMattesMutualInformation(numberOfHistogramBins=32)
    R.SetMetricSamplingStrategy(R.REGULAR)
    R.SetMetricSamplingPercentage(0.1)
    
    R.SetOptimizerAsExhaustive([4, 4, 4, 0, 0, 0])
    R.SetOptimizerScales([np.pi/4, np.pi/4, np.pi/4, 1.0, 1.0, 1.0])
    
    R.SetInitialTransform(tx, inPlace=True)
    
    t0 = time.time()
    next_tx = R.Execute(fixed, moving)
    t1 = time.time()
    
    print("Time:", t1 - t0)
    print("Best params:", next_tx.GetParameters())

test_exhaustive()
