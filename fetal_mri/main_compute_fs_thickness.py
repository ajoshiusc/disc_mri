from scipy.spatial import cKDTree
from dfsio import readdfs, writedfs
from surfproc import patch_color_attrib, view_patch_vtk

inner_file = '/deneb_disk/fetal_scan_6_13_2022/haste_rot_v2/inner.dfs'

pial_file = '/deneb_disk/fetal_scan_6_13_2022/haste_rot_v2/pial.dfs'



inner = readdfs(inner_file)
pial = readdfs(pial_file)


tree = cKDTree(pial.vertices)
d1, inds = tree.query(inner.vertices, k=1, p=2)
d = inner.vertices - pial.vertices[inds]


tree = cKDTree(inner.vertices)
d2, inds2 = tree.query(pial.vertices[inds], k=1, p=2)


thickness = (d1+d2)/2.0

inner.attributes = thickness

patch_color_attrib(inner,cmap='jet', clim=[0,1])

view_patch_vtk(inner)



