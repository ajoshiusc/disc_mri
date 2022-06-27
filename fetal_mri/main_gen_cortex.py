import nilearn.image as ni
import numpy as np
from scipy.ndimage import binary_fill_holes
import vtk
from vtk.util.numpy_support import numpy_to_vtk, vtk_to_numpy
from skimage import measure
from surfproc import smooth_patch
from dfsio import writedfs
import vtk.util.numpy_support as numpy_support

import vtk
import sys

from scipy.ndimage.morphology import grey_dilation

def MarchingCubes(image,threshold):
    '''
    http://www.vtk.org/Wiki/VTK/Examples/Cxx/Modelling/ExtractLargestIsosurface 
    '''
    mc = vtk.vtkMarchingCubes()
    mc.SetInputData(image)
    mc.ComputeNormalsOn()
    mc.ComputeGradientsOn()
    mc.SetValue(0, threshold)
    mc.Update()
    
    # To remain largest region
    confilter =vtk.vtkPolyDataConnectivityFilter()
    confilter.SetInputData(mc.GetOutput())
    confilter.SetExtractionModeToLargestRegion()
    confilter.Update()

    return confilter.GetOutput()




    
label_file = '/deneb_disk/fetal_scan_6_13_2022/haste_rot_v2/warped_labels.nii.gz'
label_dilated_file = '/deneb_disk/fetal_scan_6_13_2022/haste_rot_v2/warped_labels_dilated.nii.gz'

label_file2 = '/deneb_disk/fetal_scan_6_13_2022/haste_rot_v2/warped_labels_int16.nii.gz'

csf_file = '/deneb_disk/fetal_scan_6_13_2022/haste_rot_v2/csf.nii.gz'
cortex_file = '/deneb_disk/fetal_scan_6_13_2022/haste_rot_v2/cortex.dfs'


v = ni.load_img(label_file)

v2=ni.new_img_like(label_file,np.int16(v.get_fdata()))
v2.to_filename(label_file2)



img2=v2.get_fdata()
img2[img2 == 124]=0
img2=grey_dilation(img2,[5,5,5])

label_dilated = ni.new_img_like(label_file,np.int16(img2))
label_dilated.to_filename(label_dilated_file)

# Create CSF image
img = np.int16((v.get_fdata() != 124) & (v.get_fdata() > 0))
#img=np.int16(binary_fill_holes(img))


csf = ni.new_img_like(label_file, img)
csf = ni.reorder_img(csf)
csf.to_filename(csf_file)


ff = csf_file
reader = vtk.vtkNIFTIImageReader()
reader.SetFileName(ff)
reader.Update()
im = reader.GetOutput()
poly = MarchingCubes(im,.5)
#visualize_poly(poly)
writer = vtk.vtkSTLWriter()
writer.SetInputData(poly)
writer.SetFileName('xx.stl')
writer.Update()

pts = poly.GetPoints()
vertices = vtk_to_numpy(pts.GetData())
faces = poly.GetPolys()
faces = vtk_to_numpy(faces.GetData())
faces = faces.reshape(np.int32(len(faces) / 4), 4)
faces = faces[:, (1,3,2)]
print(vertices.shape, faces.shape)

class s:
    pass

s.faces = faces
s.vertices = vertices

s = smooth_patch(s,10)

writedfs(cortex_file,s)