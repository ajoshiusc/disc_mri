##AUM##

## Shree Ganeshaya Namah ##

mri = '/deneb_disk/disc_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA25.nii.gz'
tissue = '/deneb_disk/disc_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA25_tissue.nii.gz'

# create an inner and pial surface

import nibabel as nib
import numpy as np
from skimage import measure
import dfsio  # Make sure dfsio.py is in your Python path

from scipy.spatial import cKDTree
from surfproc import patch_color_attrib, view_patch_vtk, smooth_patch


def laplacian_smooth(verts, faces, iterations=10, lam=0.5):
    """
    Simple Laplacian smoothing for triangle meshes.
    verts: (N, 3) array of vertex positions
    faces: (M, 3) array of indices into verts
    iterations: number of smoothing iterations
    lam: smoothing factor (0 < lam < 1)
    """
    from scipy.sparse import lil_matrix

    n_verts = verts.shape[0]
    adjacency = lil_matrix((n_verts, n_verts))

    # Build adjacency matrix
    for tri in faces:
        for i in range(3):
            adjacency[tri[i], tri[(i+1)%3]] = 1
            adjacency[tri[i], tri[(i+2)%3]] = 1

    adjacency = adjacency.tocsr()

    verts_smoothed = verts.copy()
    for _ in range(iterations):
        neighbor_sum = adjacency.dot(verts_smoothed)
        neighbor_count = adjacency.sum(axis=1).A1
        # Avoid division by zero
        neighbor_count[neighbor_count == 0] = 1
        neighbor_mean = neighbor_sum / neighbor_count[:, None]
        verts_smoothed = verts_smoothed + lam * (neighbor_mean - verts_smoothed)
    return verts_smoothed

def extract_surface(tissue_data, labels, mesh_smooth_iter=10, mesh_smooth_lambda=0.5):
    # Create binary mask for the specified labels
    mask = np.isin(tissue_data, labels)

    # Extract surface using marching cubes
    verts, faces, _, _ = measure.marching_cubes(mask, level=0)

    # Apply Laplacian mesh smoothing
    verts = laplacian_smooth(verts, faces, iterations=mesh_smooth_iter, lam=mesh_smooth_lambda)

    return verts, faces

# File paths
'''
week = 25

mri_path = f'/deneb_disk/disc_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA{week}.nii.gz'
tissue_path = f'/deneb_disk/disc_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA{week}_tissue.nii.gz'

# Load tissue segmentation
tissue_img = nib.load(tissue_path)
tissue_data = tissue_img.get_fdata()

# Define label sets (update these based on your segmentation schema)
inner_labels = list(range(1, 126))
inner_labels.remove(124)
inner_labels.remove(112)
inner_labels.remove(113)

pial_labels = list(range(1, 126))
pial_labels.remove(124)  # Assuming label 1 is the inner surface

# Extract and smooth surfaces
inner_verts, inner_faces = extract_surface(
    tissue_data, inner_labels, mesh_smooth_iter=10, mesh_smooth_lambda=0.5)
pial_verts, pial_faces = extract_surface(
    tissue_data, pial_labels, mesh_smooth_iter=10, mesh_smooth_lambda=0.5)

# Save surfaces

class s:
    pass

s.faces = inner_faces
s.vertices = inner_verts

dfsio.writedfs(f'{week}_week_inner_surface.dfs', s)



s.faces = pial_faces
s.vertices = pial_verts
dfsio.writedfs(f'{week}_week_pial_surface.dfs', s)

print("Saved: inner_surface.dfs and pial_surface.dfs")

'''

# plot the surfaces and save as png files
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
def plot_surface(verts, faces, title, filename):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.set_title(title)
    ax.plot_trisurf(verts[:, 0], verts[:, 1], verts[:, 2], triangles=faces, cmap='viridis', edgecolor='none')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    plt.savefig(filename)
    plt.close()

'''
# Plot and save inner surface
plot_surface(inner_verts, inner_faces, 'Inner Surface', f'{week}_week_inner_surface.png')
# Plot and save pial surface
plot_surface(pial_verts, pial_faces, 'Pial Surface', f'{week}_week_pial_surface.png')
# Print completion message
print(f"Surface plots saved as {week}_week_inner_surface.png and {week}_week_pial_surface.png")
'''

# Loop over weeks 21 to 35
for week in range(21, 36):
    mri_path = f'/deneb_disk/disc_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA{week}.nii.gz'
    tissue_path = f'/deneb_disk/disc_mri/fetal_atlas/CRL_FetalBrainAtlas_2017v3/STA{week}_tissue.nii.gz'

    # Load tissue segmentation
    tissue_img = nib.load(tissue_path)
    tissue_data = tissue_img.get_fdata()

    # Define label sets (update these based on your segmentation schema)
    inner_labels = list(range(1, 126))
    inner_labels.remove(124)
    inner_labels.remove(112)
    inner_labels.remove(113)

    pial_labels = list(range(1, 126))
    pial_labels.remove(124)  # Assuming label 1 is the inner surface

    # Extract and smooth surfaces
    inner_verts, inner_faces = extract_surface(
        tissue_data, inner_labels, mesh_smooth_iter=10, mesh_smooth_lambda=0.5)
    pial_verts, pial_faces = extract_surface(
        tissue_data, pial_labels, mesh_smooth_iter=10, mesh_smooth_lambda=0.5)

    # Save surfaces
    class s:
        pass

    s.faces = inner_faces
    s.vertices = inner_verts
    dfsio.writedfs(f'{week}_week_inner_surface.dfs', s)

    s.faces = pial_faces
    s.vertices = pial_verts
    dfsio.writedfs(f'{week}_week_pial_surface.dfs', s)

    print(f"Saved: {week}_week_inner_surface.dfs and {week}_week_pial_surface.dfs")

    # Plot and save surfaces
    plot_surface(inner_verts, inner_faces, 'Inner Surface', f'{week}_week_inner_surface.png')
    plot_surface(pial_verts, pial_faces, 'Pial Surface', f'{week}_week_pial_surface.png')
    print(f"Surface plots saved as {week}_week_inner_surface.png and {week}_week_pial_surface.png")


    inner = dfsio.readdfs(f'{week}_week_inner_surface.dfs')
    pial = dfsio.readdfs(f'{week}_week_pial_surface.dfs')


    tree = cKDTree(pial.vertices)
    d1, inds = tree.query(inner.vertices, k=1, p=2)
    d = inner.vertices - pial.vertices[inds]


    tree = cKDTree(inner.vertices)
    d2, inds2 = tree.query(pial.vertices[inds], k=1, p=2)


    thickness = (d1+d2)/2.0

    inner.attributes = thickness

    patch_color_attrib(inner, cmap='jet', clim=[0, 5])

    #inner = smooth_patch(inner, 50)

    view_patch_vtk(inner, outfile=f'{week}_week_inner_surface_view.png', show=False)
    dfsio.writedfs(f'{week}_week_inner_depth.dfs', inner)
    print(f"Computed and saved inner surface depth for week {week}.")


    tree = cKDTree(inner.vertices)
    d1, inds = tree.query(pial.vertices, k=1, p=2)
    d = pial.vertices - inner.vertices[inds]


    tree = cKDTree(pial.vertices)
    d2, inds2 = tree.query(inner.vertices[inds], k=1, p=2)


    thickness = (d1+d2)/2.0

    pial.attributes = thickness
    patch_color_attrib(pial, cmap='jet', clim=[0, 5])
    #pial = smooth_patch(pial, 50)
    view_patch_vtk(pial, outfile=f'{week}_week_pial_surface_view.png', show=False)
    dfsio.writedfs(f'{week}_week_pial_depth.dfs', pial)
    print(f"Computed and saved pial surface depth for week {week}.")




# End of script
