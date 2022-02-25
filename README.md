# DISC MRI
## T1 to T1 registration
Please try main_t12t1_brain_reg.m
There are comments in the code that can help you run it on different scans.

This is rigid registration between two scans of the same subject. There is also option of affine registration, but the rigid registration seemed to work well for this set of scans. There might be situations where you might want to try affine registration.
For the input T1 images, I ran brainsuite on them upto tissue classification. This generates pvc frac files, giving us fraction of gm/wm/csf at each voxel. The skull is also removed.
Now starting from the two pvc frac files I ran rigid registration with sum of squared difference as cost function. 
Then the generated rigid registration is applied on the original T1 MRI. 

There are multiple ways to do this but given that the first few steps in BrainSuite are very fast, I think this is the easiest way to get accurate and reliable results.

## Super resolution 2D to 3D
