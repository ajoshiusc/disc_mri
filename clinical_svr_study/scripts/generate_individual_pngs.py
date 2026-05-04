import csv
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import nibabel as nib
from nilearn import plotting
from nilearn.image import crop_img
import os

manifest_file = 'outputs/figures/representative_case_figure_manifest.csv'
out_dir = Path('outputs/figures/individual_pngs')
out_dir.mkdir(parents=True, exist_ok=True)

with open(manifest_file, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        case_id = row['case_id']
        fig = row['figure']
        
        paths = {
            'svr': row['svr_path'],
            'raw_axial': row['raw_axial_path'],
            'raw_coronal': row['raw_coronal_path'],
            'raw_sagittal': row['raw_sagittal_path']
        }
        
        for key, p in paths.items():
            if p and os.path.exists(p):
                try:
                    img = nib.load(p)
                    img = nib.as_closest_canonical(img)
                    img = crop_img(img, rtol=1e-3)
                    
                    # Strip rotation from affine so slices display straight (not tilted)
                    data = img.get_fdata()
                    affine = img.affine
                    zooms = img.header.get_zooms()
                    new_affine = np.zeros((4, 4))
                    new_affine[0, 0] = zooms[0] if affine[0, 0] > 0 else -zooms[0]
                    new_affine[1, 1] = zooms[1] if affine[1, 1] > 0 else -zooms[1]
                    new_affine[2, 2] = zooms[2] if affine[2, 2] > 0 else -zooms[2]
                    new_affine[3, 3] = 1.0
                    new_affine[:3, 3] = affine[:3, 3]
                    img = nib.Nifti1Image(data, new_affine)
                    
                    out_png = out_dir / f"case_{case_id}_{key}.png"
                    
                    # using plot_anat, which plots ortho (x, y, z) by default
                    display = plotting.plot_anat(
                        img, 
                        display_mode='ortho', 
                        draw_cross=False, 
                        annotate=False, 
                        colorbar=False,
                        black_bg=True
                    )
                    display.savefig(str(out_png), dpi=300, bbox_inches='tight', pad_inches=0.0)
                    display.close()
                    print(f"Generated {out_png}")
                except Exception as e:
                    print(f"Failed for {p}: {e}")

