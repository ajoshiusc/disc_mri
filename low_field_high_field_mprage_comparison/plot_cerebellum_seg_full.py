import numpy as np
import nibabel as nib
import matplotlib.pyplot as plt
import os
import matplotlib
matplotlib.use('Agg')

def plot_cerebellum(subject_id=5, param="1e-14"):
    out_dir_1 = f"/deneb_disk/3T_vs_low_field/freesurfer_processed_subjects/subjects/subj_{subject_id}_vol1_LF_{param}"
    out_dir_2 = f"/deneb_disk/3T_vs_low_field/freesurfer_processed_subjects/subjects/subj_{subject_id}_vol2_LF_{param}"
    
    seg_file_1 = os.path.join(out_dir_1, "mri", "aparc+aseg.mgz")
    anat_file_1 = os.path.join(out_dir_1, "mri", "norm.mgz")
    if not os.path.exists(anat_file_1):
        anat_file_1 = os.path.join(out_dir_1, "mri", "brain.mgz")
        if not os.path.exists(anat_file_1):
            anat_file_1 = os.path.join(out_dir_1, "mri", "T1.mgz")
            
    seg_file_2 = os.path.join(out_dir_2, "mri", "aparc+aseg.mgz")
    anat_file_2 = os.path.join(out_dir_2, "mri", "norm.mgz")
    if not os.path.exists(anat_file_2):
        anat_file_2 = os.path.join(out_dir_2, "mri", "brain.mgz")
        if not os.path.exists(anat_file_2):
            anat_file_2 = os.path.join(out_dir_2, "mri", "T1.mgz")
    
    anat1 = nib.load(anat_file_1).get_fdata()
    seg1 = nib.load(seg_file_1).get_fdata()
    anat2 = nib.load(anat_file_2).get_fdata()
    seg2 = nib.load(seg_file_2).get_fdata()
    
    wm1 = (seg1 == 7)
    ctx1 = (seg1 == 8)
    wm2 = (seg2 == 7)
    ctx2 = (seg2 == 8)
    
    x_coords = np.where(wm1 | ctx1)[0]
    y_coords = np.where(wm1 | ctx1)[1]
    
    sag_slice = int(np.median(x_coords))
    cor_slice = int(np.median(y_coords))
    
    fig, axes = plt.subplots(2, 2, figsize=(10, 10))
    fig.suptitle(f"Subject {subject_id} Left Cerebellum Segmentation at 0.55T\nFull FOV (Red: White Matter, Blue: Cortex)", fontsize=16)
    
    from matplotlib.colors import ListedColormap
    cmap_red = ListedColormap(['red'])
    cmap_blue = ListedColormap(['cyan'])
    
    def overlay_seg(ax, anat, wm, ctx, slice_idx, axis):
        if axis == 0:
            # Let's rotate 90 degrees strictly clockwise (k=-1), but we must then flip left-right
            # This puts the subject facing left, head up.
            a = np.array(anat[slice_idx, :, :])#, k=1)
            w = np.array(wm[slice_idx, :, :])#, k=1)
            c = np.array(ctx[slice_idx, :, :])#, k=1)
            
            # Now let's try flipping vertically since standard rot90(k=1) on mgz makes head point down
            # Actually, standard mgz: rot90 k=1 makes head upright, but facing left
            
        elif axis == 1:
            a = np.rot90(anat[:, slice_idx, :], k=1)
            w = np.rot90(wm[:, slice_idx, :], k=1)
            c = np.rot90(ctx[:, slice_idx, :], k=1)
            
        ax.imshow(a, cmap='gray', vmin=0, vmax=np.percentile(a[a>0], 99) if np.any(a>0) else 255, interpolation='none')
        
        ax.imshow(np.ma.masked_where(~w, w), cmap=cmap_red, alpha=0.5, interpolation='none')
        ax.imshow(np.ma.masked_where(~c, c), cmap=cmap_blue, alpha=0.5, interpolation='none')
        
        ax.axis('off')

    overlay_seg(axes[0, 0], anat1, wm1, ctx1, sag_slice, axis=0)
    axes[0, 0].set_title("Session 1: Sagittal Slice")
    
    overlay_seg(axes[0, 1], anat1, wm1, ctx1, cor_slice, axis=1)
    axes[0, 1].set_title("Session 1: Coronal Slice")

    overlay_seg(axes[1, 0], anat2, wm2, ctx2, sag_slice, axis=0)
    axes[1, 0].set_title("Session 2: Sagittal Slice")
    
    overlay_seg(axes[1, 1], anat2, wm2, ctx2, cor_slice, axis=1)
    axes[1, 1].set_title("Session 2: Coronal Slice")
    
    plt.tight_layout()
    plt.savefig("subject5_cerebellum_full_fov.png", dpi=300, bbox_inches='tight')
    print("Saved figure as subject5_cerebellum_full_fov.png")

plot_cerebellum(subject_id=5)
