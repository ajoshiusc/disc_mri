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
    anat_file_1 = os.path.join(out_dir_1, "mri", "T1.mgz")
    
    seg_file_2 = os.path.join(out_dir_2, "mri", "aparc+aseg.mgz")
    anat_file_2 = os.path.join(out_dir_2, "mri", "T1.mgz")
    
    anat1 = nib.load(anat_file_1).get_fdata()
    seg1 = nib.load(seg_file_1).get_fdata()
    anat2 = nib.load(anat_file_2).get_fdata()
    seg2 = nib.load(seg_file_2).get_fdata()
    
    wm1 = (seg1 == 7)
    ctx1 = (seg1 == 8)
    wm2 = (seg2 == 7)
    ctx2 = (seg2 == 8)
    
    # Calculate crop bounds to center on the cerebellum
    x_coords = np.where(wm1 | ctx1)[0]
    y_coords = np.where(wm1 | ctx1)[1]
    z_coords = np.where(wm1 | ctx1)[2]
    
    sag_slice = int(np.median(x_coords))
    cor_slice = int(np.median(y_coords))
    
    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    fig.suptitle(f"Subject {subject_id} Left Cerebellum Segmentation at 0.55T\nRed: White Matter, Blue: Cortex", fontsize=16)
    
    def overlay_seg(ax, anat, wm, ctx, slice_idx, axis):
        if axis == 0:
            a = np.rot90(anat[slice_idx, :, :])
            w = np.rot90(wm[slice_idx, :, :])
            c = np.rot90(ctx[slice_idx, :, :])
        elif axis == 1:
            a = np.rot90(anat[:, slice_idx, :])
            w = np.rot90(wm[:, slice_idx, :])
            c = np.rot90(ctx[:, slice_idx, :])
            
        ax.imshow(a, cmap='gray', vmin=0, vmax=np.percentile(a, 99))
        
        # Overlay colors with higher opacity for clarity
        overlay = np.zeros((*a.shape, 4))
        overlay[w, :] = [1, 0, 0, 0.4] 
        overlay[c, :] = [0, 0.5, 1, 0.4] 
        
        # Add outlines
        ax.contour(w, colors='red', linewidths=0.5)
        ax.contour(c, colors='blue', linewidths=0.5)
        
        ax.imshow(overlay, interpolation='none')
        
        # Smart dynamic zooming
        ax.set_ylim(a.shape[0]-20, a.shape[0]-140) 
        if axis == 0:
            ax.set_xlim(30, 200)
        else:
            ax.set_xlim(a.shape[1]//2 - 30, a.shape[1] - 30)
            
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
    plt.savefig("subject5_cerebellum_misclassification.png", dpi=300, bbox_inches='tight')
    print("Saved figure as subject5_cerebellum_misclassification.png")

plot_cerebellum(subject_id=5)
