import numpy as np
import nibabel as nib

def check_subject_fov(n):
    for sess in (1, 2):
        out_dir = f"/deneb_disk/3T_vs_low_field/freesurfer_processed_subjects/subjects/subj_{n}_vol{sess}_LF_1e-14"
        anat_file = out_dir + "/mri/T1.mgz"
        seg_file = out_dir + "/mri/aparc+aseg.mgz"
        
        try:
            seg_img = nib.load(seg_file)
            seg_data = seg_img.get_fdata()
            
            # Find cerebellum voxels (labels 7, 8, 46, 47)
            cerebellum_mask = np.isin(seg_data, [7, 8, 46, 47])
            
            # Find image dimensions
            shape = seg_data.shape
            
            if not np.any(cerebellum_mask):
                continue
                
            # Find min and max indices along the Z-axis (usually axis 1 or 2 depending on orientation)
            # Let's check all axes
            coords = np.argwhere(cerebellum_mask)
            min_coords = coords.min(axis=0)
            max_coords = coords.max(axis=0)
            
            print(f"Subj {n} Sess {sess}:")
            print(f"  Shape: {shape}")
            print(f"  Cerebellum min coords: {min_coords}")
            print(f"  Cerebellum max coords: {max_coords}")
            
            # Let's also check brain stem (label 16) bounds
            stem_mask = np.isin(seg_data, [16])
            if np.any(stem_mask):
                stem_coords = np.argwhere(stem_mask)
                print(f"  Brain Stem max coords: {stem_coords.max(axis=0)}")
                
        except Exception as e:
            print(f"Could not load {out_dir}: {e}")

print("Checking Subject 1 (Subject Index 0)")
check_subject_fov(1)

print("\nChecking Subject 5 (Subject Index 4)")
check_subject_fov(5)

