import numpy as np

roi_vols_lf = np.load("freesurfer_low_field.npz")["roi_vols"]
label_ids = np.load("freesurfer_3T.npz")["label_ids"]

roi_vols_lf = roi_vols_lf[:, :, 0, 1:-1]
roi_vols_lf = roi_vols_lf.reshape(2, -1)
valid_label_ids = label_ids[1:-1]

print("Subject 5 (index 4) Left Cerebellum White Matter (7):")
idx = 4 * len(valid_label_ids) + np.where(valid_label_ids == 7)[0][0]
print(f"  Sess 1: {roi_vols_lf[0, idx]} mm3")
print(f"  Sess 2: {roi_vols_lf[1, idx]} mm3")

idx2 = 4 * len(valid_label_ids) + np.where(valid_label_ids == 8)[0][0]
print(f"Subject 5 (index 4) Left Cerebellum Cortex (8):")
print(f"  Sess 1: {roi_vols_lf[0, idx2]} mm3")
print(f"  Sess 2: {roi_vols_lf[1, idx2]} mm3")

