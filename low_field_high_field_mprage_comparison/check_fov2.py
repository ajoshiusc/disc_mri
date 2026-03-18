import numpy as np
import nibabel as nib

def check_subject_fov(n):
    for sess in (1, 2):
        out_dir = f"/deneb_disk/3T_vs_low_field/freesurfer_processed_subjects/subjects/subj_{n}_vol{sess}_LF_1e-14"
        anat_file = out_dir + "/mri/T1.mgz"
        seg_file = out_dir + "/mri/aparc+aseg.mgz"
        
        try:
            anat_img = nib.load(anat_file)
            anat_data = anat_img.get_fdata()
            
            seg_img = nib.load(seg_file)
            seg_data = seg_img.get_fdata()
            
            # Find image tissue bounds (> 10 intensity)
            tissue_mask = anat_data > 10
            if np.any(tissue_mask):
                tissue_coords = np.argwhere(tissue_mask)
                t_min = tissue_coords.min(axis=0)
                t_max = tissue_coords.max(axis=0)
                
            # Find cerebellum voxels
            cerebellum_mask = np.isin(seg_data, [7, 8, 46, 47])
            if np.any(cerebellum_mask):
                c_coords = np.argwhere(cerebellum_mask)
                c_min = c_coords.min(axis=0)
                c_max = c_coords.max(axis=0)
                
            print(f"Subj {n} Sess {sess}:")
            print(f"  Tissue bounding box min: {t_min}")
            print(f"  Tissue bounding box max: {t_max}")
            print(f"  Cerebellum bounds min:   {c_min}")
            print(f"  Cerebellum bounds max:   {c_max}")
            
            # Z is usually axis 1 or 2. Let's see how close they are
            diff_min = c_min - t_min
            diff_max = t_max - c_max
            print(f"  Distance from cerebellum to tissue edge (min): {diff_min}")
            print(f"  Distance from cerebellum to tissue edge (max): {diff_max}")
                
        except Exception as e:
            pass

print("Checking Subject 1 (Subject Index 0)")
check_subject_fov(1)

print("\nChecking Subject 5 (Subject Index 4)")
check_subject_fov(5)
