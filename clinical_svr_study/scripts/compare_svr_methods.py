import os
import numpy as np
import nibabel as nib
import pandas as pd
import matplotlib.pyplot as plt
from nilearn import plotting

def main():
    method1_dir = '/home/ajoshi/project2_ajoshi_27/data/clinical_svr_chla_data/svr.old4/nifti_svr/'
    method2_dir = '/home/ajoshi/project2_ajoshi_27/data/clinical_svr_chla_data/svr_aligned_randomized_31/'
    csv_file = 'outputs/paired_case_table.csv'
    output_dir = 'outputs/figures/comparisons'

    os.makedirs(output_dir, exist_ok=True)

    df = pd.read_csv(csv_file)

    for index, row in df.iterrows():
        case_id = int(row['case_id'])
        rand_id = int(row['svr_randomized_id'])
        
        # Handle different capitalization of SVR directory names
        img1_path = None
        for prefix in ['SVR', 'Svr', 'svr']:
            candidate_path = os.path.join(method1_dir, f'{prefix}{case_id:03d}', 'output.nii.gz')
            if os.path.exists(candidate_path):
                img1_path = candidate_path
                break
                
        if img1_path is None:
            # Fallback for the missing file alert below
            img1_path = os.path.join(method1_dir, f'SVR{case_id:03d}', 'output.nii.gz')
            
        img2_path = os.path.join(method2_dir, f'RND_{rand_id:04d}_SVR_aligned.nii.gz')
        
        if not os.path.exists(img1_path):
            print(f"Missing {img1_path}")
            continue
        if not os.path.exists(img2_path):
            print(f"Missing {img2_path}")
            continue
            
        fig, axes = plt.subplots(2, 1, figsize=(10, 8), facecolor='black')
        
        try:
            # Calculate 99.5th percentile for vmax to prevent dimming from extreme bright spots
            img1_data = nib.load(img1_path).get_fdata()
            img2_data = nib.load(img2_path).get_fdata()
            vmax1 = np.percentile(img1_data, 99.5)
            vmax2 = np.percentile(img2_data, 99.5)
            
            plotting.plot_anat(img1_path, axes=axes[0], title=img1_path, vmax=vmax1, draw_cross=False)
            plotting.plot_anat(img2_path, axes=axes[1], title=img2_path, vmax=vmax2, draw_cross=False)
            
            # The nilearn title defaults to white text.
            output_file = os.path.join(output_dir, f'comparison_SVR{case_id:03d}.png')
            plt.savefig(output_file, bbox_inches='tight', facecolor='black')
            plt.close(fig)
            print(f"Saved {output_file}")
        except Exception as e:
            print(f"Error plotting case {case_id}: {e}")
            plt.close(fig)

if __name__ == "__main__":
    main()
