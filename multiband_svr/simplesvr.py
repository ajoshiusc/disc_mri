#!/usr/bin/env python3
"""
svr_slice_to_volume_with_sform.py

Slice-to-volume registration (per-slice rigid) using NIfTI sform/qform affines (via nibabel)
and GPU-accelerated optimization (PyTorch). Minimal MONAI usage for intensity scaling.

Notes:
 - This is an image-domain SVR (rigid per-slice) + simple NN-splat reconstruction.
 - Affines are read from NIfTI header (prefers sform/qform).
"""
import argparse, os
import numpy as np
import nibabel as nib
import torch
import torch.nn.functional as F
from monai.transforms import ScaleIntensity

# -------------------------
# Utilities: I/O + affines
# -------------------------
def load_stack_nifti(path):
    img = nib.load(path)
    data = img.get_fdata(dtype=np.float32)   # shape: (nx, ny, nz)
    # nibabel: header.get_best_affine() prefer sform/qform
    try:
        affine = img.header.get_best_affine()
    except Exception:
        affine = img.affine
    return data, affine, img.header

def compute_world_bounds(stacks_data_affines):
    """
    stacks_data_affines: list of tuples (data_shape, affine)
      data_shape = (nx,ny,nz)
    Returns world_min, world_max (3,)
    """
    mins, maxs = [], []
    for shape, affine in stacks_data_affines:
        nx, ny, nz = shape
        # corners in voxel indices
        corners_idx = np.array([[i,j,k] for i in (0, nx-1) for j in (0, ny-1) for k in (0, nz-1)], dtype=float)
        hom = np.concatenate([corners_idx, np.ones((corners_idx.shape[0],1))], axis=1)  # (8,4)
        corners_world = (affine @ hom.T).T[:, :3]
        mins.append(corners_world.min(axis=0))
        maxs.append(corners_world.max(axis=0))
    mn = np.vstack(mins).min(axis=0)
    mx = np.vstack(maxs).max(axis=0)
    return mn, mx

def make_reference_affine_and_shape(world_min, world_max, spacing):
    # create axis-aligned reference grid with isotropic spacing
    padded_min = world_min - spacing
    padded_max = world_max + spacing
    extent = padded_max - padded_min
    nx = int(np.ceil(extent[0]/spacing)) + 1
    ny = int(np.ceil(extent[1]/spacing)) + 1
    nz = int(np.ceil(extent[2]/spacing)) + 1
    shape = (nx, ny, nz)
    # reference affine: voxel->world: diag(spacing) and origin padded_min
    affine = np.eye(4, dtype=float)
    affine[0,0] = spacing
    affine[1,1] = spacing
    affine[2,2] = spacing
    affine[:3,3] = padded_min
    return affine, shape

# -------------------------
# Slice world coordinates
# -------------------------
def slice_world_coords(nx, ny, k, affine):
    # build grid of voxel indices (i: 0..nx-1) (x), (j:0..ny-1) (y) for fixed k
    i = np.arange(nx)
    j = np.arange(ny)
    grid_x, grid_y = np.meshgrid(i, j, indexing='xy')  # shape (ny, nx)
    ijk = np.stack([grid_x.ravel(), grid_y.ravel(), np.full(grid_x.size, k)], axis=1)  # (N,3)
    hom = np.concatenate([ijk, np.ones((ijk.shape[0],1))], axis=1)  # (N,4)
    pts_world = (affine @ hom.T).T[:, :3]  # (N,3)
    return pts_world, (ny, nx)  # return also (H,W)

# -------------------------
# Torch-based optimization
# -------------------------
def rodrigues_rotate_torch(p, rotvec):
    # rotvec (3,), p (N,3)
    theta = torch.norm(rotvec) + 1e-12
    k = rotvec / theta
    k = k.view(1,3)  # (1,3)
    cos = torch.cos(theta)
    sin = torch.sin(theta)
    p_cos = p * cos
    k_cross_p = torch.cross(k.repeat(p.size(0),1), p, dim=1)
    term2 = k_cross_p * sin
    k_dot_p = torch.sum(k * p, dim=1, keepdim=True)
    term3 = k * k_dot_p * (1 - cos)
    return p_cos + term2 + term3

def apply_rigid_torch(pts, rot, trans):
    if torch.norm(rot) < 1e-8:
        return pts + trans.view(1,3)
    return rodrigues_rotate_torch(pts, rot) + trans.view(1,3)

def ncc_loss(a, b, eps=1e-8):
    a_mean = a.mean(); b_mean = b.mean()
    a_c = a - a_mean; b_c = b - b_mean
    num = (a_c * b_c).sum()
    den = torch.sqrt((a_c*a_c).sum() * (b_c*b_c).sum() + eps)
    return num / (den + 1e-12)

def optimize_slice_on_gpu(slice_img, pts_world_np, ref_volume_t, ref_affine, ref_shape, steps=150, lr=0.05, device='cuda'):
    """
    slice_img: (H,W) numpy float32 (we expect shape matching pts_world mapping: H rows, W cols)
    pts_world_np: (N,3) world coordinates for each pixel (x,y,z)
    ref_volume_t: torch tensor (1,1,D,H,W) on device with reference volume (z,y,x)
    ref_affine: reference affine (voxel->world)
    ref_shape: (nx,ny,nz)
    returns (rot_np, trans_np), best_ncc
    """
    device = torch.device(device if torch.cuda.is_available() else 'cpu')
    # prepare tensors
    pts_world = torch.tensor(pts_world_np, dtype=torch.float32, device=device)  # (N,3)
    target = torch.tensor(slice_img, dtype=torch.float32, device=device)
    # normalize target
    target = (target - target.mean()) / (target.std() + 1e-8)
    rot = torch.zeros(3, requires_grad=True, device=device)
    trans = torch.zeros(3, requires_grad=True, device=device)
    opt = torch.optim.Adam([rot, trans], lr=lr)
    # precompute inverse reference affine to transform world->ref_voxel
    inv_ref_affine = np.linalg.inv(ref_affine)
    inv_ref_affine_t = torch.tensor(inv_ref_affine, dtype=torch.float32, device=device)
    nx, ny, nz = ref_shape
    best_ncc = -1.0
    best_state = None
    H, W = target.shape
    for it in range(steps):
        opt.zero_grad()
        transformed_world = apply_rigid_torch(pts_world, rot, trans)  # (N,3)
        ones = torch.ones((transformed_world.shape[0],1), device=device)
        hom = torch.cat([transformed_world, ones], dim=1)  # (N,4)
        # voxel coords in ref = inv_ref_affine @ hom.T
        voxel = torch.matmul(inv_ref_affine_t, hom.T).T[:, :3]  # (N,3) in (x,y,z) voxel indices
        # convert to normalized coords for grid_sample; grid_sample expects coords in [-1,1] and order (x, y, z)
        x = voxel[:,0]; y = voxel[:,1]; z = voxel[:,2]
        x_n = (x / (nx - 1)) * 2.0 - 1.0
        y_n = (y / (ny - 1)) * 2.0 - 1.0
        z_n = (z / (nz - 1)) * 2.0 - 1.0
        grid = torch.stack([x_n, y_n, z_n], dim=1).view(1,1,H,W,3)  # (N,B,D_out,H,W,3) but here D_out=1
        sampled = F.grid_sample(ref_volume_t, grid, mode='bilinear', padding_mode='border', align_corners=True)
        sampled2d = sampled.squeeze(0).squeeze(0).squeeze(1)  # (H,W)
        sampled_n = (sampled2d - sampled2d.mean()) / (sampled2d.std() + 1e-8)
        # negative NCC loss
        ncc = ncc_loss(sampled_n, target)
        loss = -ncc
        loss.backward()
        opt.step()
        ncc_val = float(ncc.detach().cpu().numpy())
        if ncc_val > best_ncc:
            best_ncc = ncc_val
            best_state = (rot.detach().cpu().numpy().copy(), trans.detach().cpu().numpy().copy())
        # optional lr decay
        if (it+1) % 75 == 0:
            for g in opt.param_groups:
                g['lr'] *= 0.5
    return best_state, best_ncc

# -------------------------
# Reconstruction: NN splatting
# -------------------------
def reconstruct_from_slices_nn(slices_meta, transforms, ref_affine, ref_shape):
    nx, ny, nz = ref_shape
    accum = np.zeros((nz, ny, nx), dtype=np.float64)  # (z,y,x)
    weight = np.zeros_like(accum)
    inv_ref_affine = np.linalg.inv(ref_affine)
    for meta, tr in zip(slices_meta, transforms):
        if tr is None:
            continue
        rot, trans = tr
        H, W = meta['shape']
        # build pts_world
        pts_world, _ = slice_world_coords(meta['nx'], meta['ny'], meta['k'], meta['affine'])
        # apply rot/trans (numpy Rodrigues -> matrix)
        angle = np.linalg.norm(rot)
        if angle < 1e-12:
            R = np.eye(3)
        else:
            u = rot / angle
            ux,uy,uz = u
            K = np.array([[0,-uz,uy],[uz,0,-ux],[-uy,ux,0]])
            R = np.eye(3)*np.cos(angle) + (1-np.cos(angle))*np.outer(u,u) + np.sin(angle)*K
        pts_rot = (R @ pts_world.T).T + trans.reshape(1,3)
        # world -> ref voxels
        hom = np.concatenate([pts_rot, np.ones((pts_rot.shape[0],1))], axis=1)
        vox = (inv_ref_affine @ hom.T).T[:, :3]  # (N,3) x,y,z
        coords = np.round(vox).astype(int)
        valid = (coords[:,0] >= 0) & (coords[:,0] < nx) & (coords[:,1] >= 0) & (coords[:,1] < ny) & (coords[:,2] >= 0) & (coords[:,2] < nz)
        vals = meta['img'].ravel()[valid]
        c = coords[valid]
        # accum indexing: accum[z,y,x]
        accum[c[:,2], c[:,1], c[:,0]] += vals
        weight[c[:,2], c[:,1], c[:,0]] += 1.0
    vol = np.zeros_like(accum)
    nzmask = weight > 0
    vol[nzmask] = accum[nzmask] / weight[nzmask]
    return vol  # (z,y,x) numpy

# -------------------------
# Pipeline
# -------------------------
def svr_pipeline(stack_paths, output_path, out_spacing=1.0, n_outer=2, slice_steps=150, slice_lr=0.05, ncc_thresh=0.15, device='cuda'):
    # 1) load stacks, affines, headers
    stacks = []
    meta_list = []
    for p in stack_paths:
        data, aff, hdr = load_stack_nifti(p)
        nx, ny, nz = data.shape
        stacks.append((data, aff))
        meta_list.append({'data': data, 'affine': aff, 'nx': nx, 'ny': ny, 'nz': nz})
    # 2) compute world bounds
    shapes_affs = [((m['nx'], m['ny'], m['nz']), m['affine']) for m in meta_list]
    wmin, wmax = compute_world_bounds(shapes_affs)
    ref_affine, ref_shape = make_reference_affine_and_shape(wmin, wmax, out_spacing)
    nxr, nyr, nzr = ref_shape
    print("Reference shape (nx,ny,nz):", ref_shape)
    # 3) initial volume by naive NN forward-mapping average (map each stack voxel center to ref vox)
    # For speed: map voxel centers of each stack to ref voxel indices and splat
    accum = np.zeros((nzr, nyr, nxr), dtype=np.float64)
    weight = np.zeros_like(accum)
    inv_ref_aff = np.linalg.inv(ref_affine)
    for m in meta_list:
        data = m['data']
        nx, ny, nz = m['nx'], m['ny'], m['nz']
        # build all voxel indices
        ix = np.arange(nx); iy = np.arange(ny); iz = np.arange(nz)
        gx, gy, gz = np.meshgrid(ix, iy, iz, indexing='xy')  # shapes (ny,nx,nz) careful
        # produce (N,3) voxel coords in stack indexing (i,j,k) -> flatten
        ijk = np.stack([gx.ravel(), gy.ravel(), gz.ravel()], axis=1)  # (N,3)
        hom = np.concatenate([ijk, np.ones((ijk.shape[0],1))], axis=1)
        pts_world = (m['affine'] @ hom.T).T[:, :3]
        vox_ref = (inv_ref_aff @ hom.T).T[:, :3]
        coords = np.round(vox_ref).astype(int)
        valid = (coords[:,0] >= 0) & (coords[:,0] < nxr) & (coords[:,1] >= 0) & (coords[:,1] < nyr) & (coords[:,2] >= 0) & (coords[:,2] < nzr)
        vals = data.ravel()[valid]
        c = coords[valid]
        accum[c[:,2], c[:,1], c[:,0]] += vals
        weight[c[:,2], c[:,1], c[:,0]] += 1.0
    init_vol = np.zeros_like(accum)
    mask = weight > 0
    init_vol[mask] = accum[mask] / weight[mask]
    volume = init_vol.astype(np.float32)  # (z,y,x)
    # build slice list metadata
    slices = []
    for idx, m in enumerate(meta_list):
        data = m['data']
        nx, ny, nz = m['nx'], m['ny'], m['nz']
        for k in range(nz):
            # slice image as (H,W) = (ny, nx) using transpose to match pixel row/col
            sl = data[:,:,k].T.copy()
            slices.append({'img': sl, 'affine': m['affine'], 'nx': nx, 'ny': ny, 'k': k, 'src_idx': idx})
    print("Total slices:", len(slices))
    # outer iterations
    transforms = [None] * len(slices)
    device = device if torch.cuda.is_available() else 'cpu'
    for outer in range(n_outer):
        print(f"\n-- Outer iter {outer+1}/{n_outer} --")
        # convert ref volume to torch tensor (z,y,x) -> (1,1,D,H,W)
        vol_t = torch.tensor(volume[np.newaxis, np.newaxis, :, :, :], dtype=torch.float32, device=device)
        ref_info = {'affine': ref_affine, 'shape': ref_shape}
        for i, s in enumerate(slices):
            pts_world, (H, W) = slice_world_coords(s['nx'], s['ny'], s['k'], s['affine'])
            try:
                best_state, best_ncc = optimize_slice_on_gpu(s['img'], pts_world, vol_t, ref_affine, ref_shape, steps=slice_steps, lr=slice_lr, device=device)
                if best_state is None or best_ncc < ncc_thresh:
                    transforms[i] = None
                else:
                    transforms[i] = best_state
                if (i % 100) == 0:
                    print(f"slice {i}/{len(slices)} - NCC {best_ncc:.3f} -> {'kept' if transforms[i] is not None else 'drop'}")
            except Exception as e:
                transforms[i] = None
                print("slice opt failed:", e)
        # reconstruct
        vol_new = reconstruct_from_slices_nn(slices, transforms, ref_affine, ref_shape)
        # fill holes from previous volume if needed
        mask_new = vol_new > 0
        volume[mask_new] = vol_new[mask_new]
        print("Reconstructed mean:", float(volume[volume>0].mean()) if (volume>0).sum()>0 else 0.0)
    # save NIfTI with ref_affine and shape
    # convert (z,y,x) -> nibabel expects (nx,ny,nz) ordering for data array
    save_arr = np.transpose(volume, (2,1,0))  # (nx,ny,nz)
    out_img = nib.Nifti1Image(save_arr.astype(np.float32), affine=ref_affine)
    nib.save(out_img, output_path)
    print("Saved:", output_path)
    return transforms

# -------------------------
# CLI
# -------------------------
def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--stacks', nargs='+', required=True, help='Input NIfTI stack files')
    p.add_argument('--output', required=True, help='Output reconstructed NIfTI')
    p.add_argument('--spacing', type=float, default=1.0, help='Reference isotropic spacing (mm)')
    p.add_argument('--nouter', type=int, default=2, help='Outer iterations')
    p.add_argument('--slicesteps', type=int, default=150, help='Optimizer steps per slice')
    p.add_argument('--slicelr', type=float, default=0.05, help='Per-slice optimizer LR')
    p.add_argument('--ncc', type=float, default=0.15, help='NCC threshold to keep slice')
    p.add_argument('--device', type=str, default='cuda', help='torch device')
    return p.parse_args()

if __name__ == '__main__':
    args = parse_args()
    transforms = svr_pipeline(args.stacks, args.output, out_spacing=args.spacing, n_outer=args.nouter,
                              slice_steps=args.slicesteps, slice_lr=args.slicelr, ncc_thresh=args.ncc,
                              device=args.device)

