from scipy.spatial import cKDTree
from dfsio import readdfs, writedfs
from surfproc import patch_color_attrib, view_patch_vtk, smooth_patch

inner_file = '/deneb_disk/fetal_scan_8_7_2022/haste_brain_rot/inner.dfs'

pial_file = '/deneb_disk/fetal_scan_8_7_2022/haste_brain_rot/pial.dfs'

out_file = '/deneb_disk/fetal_scan_8_7_2022/haste_brain_rot/inner_depth.dfs'


inner = readdfs(inner_file)
pial = readdfs(pial_file)


tree = cKDTree(pial.vertices)
d1, inds = tree.query(inner.vertices, k=1, p=2)
d = inner.vertices - pial.vertices[inds]


tree = cKDTree(inner.vertices)
d2, inds2 = tree.query(pial.vertices[inds], k=1, p=2)


thickness = (d1+d2)/2.0

inner.attributes = thickness

patch_color_attrib(inner, cmap='jet', clim=[0, 5])

inner = smooth_patch(inner, 50)

view_patch_vtk(inner)

writedfs(out_file, inner)
