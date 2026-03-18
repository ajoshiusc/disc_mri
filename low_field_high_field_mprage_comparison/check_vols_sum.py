import numpy as np

roi_vols_lf = np.load("freesurfer_low_field.npz")["roi_vols"]
label_ids = np.load("freesurfer_3T.npz")["label_ids"]

roi_vols_lf = roi_vols_lf[:, :, 0, 1:-1]
roi_vols_lf = roi_vols_lf.reshape(2, -1)
valid_label_ids = label_ids[1:-1]

print("Subject 5 (index 4) Left Cerebellum:")
wm_idx = 4 * len(valid_label_ids) + np.where(valid_label_ids == 7)[0][0]
ctx_idx = 4 * len(valid_label_ids) + np.where(valid_label_ids == 8)[0][0]

s1_wm, s2_wm = roi_vols_lf[0, wm_idx], roi_vols_lf[1, wm_idx]
s1_ctx, s2_ctx = roi_vols_lf[0, ctx_idx], roi_vols_lf[1, ctx_idx]

print(f"  Sess 1 WM + Ctx: {s1_wm + s1_ctx} mm3 (WM: {s1_wm}, Ctx: {s1_ctx})")
print(f"  Sess 2 WM + Ctx: {s2_wm + s2_ctx} mm3 (WM: {s2_wm}, Ctx: {s2_ctx})")
print(f"  Difference in sum: {((s1_wm + s1_ctx) - (s2_wm + s2_ctx))/1000.0} cm3")

print("\nSubject 1 (index 0) Left Cerebellum:")
wm_idx = 0 * len(valid_label_ids) + np.where(valid_label_ids == 7)[0][0]
ctx_idx = 0 * len(valid_label_ids) + np.where(valid_label_ids == 8)[0][0]

s1_wm, s2_wm = roi_vols_lf[0, wm_idx], roi_vols_lf[1, wm_idx]
s1_ctx, s2_ctx = roi_vols_lf[0, ctx_idx], roi_vols_lf[1, ctx_idx]

print(f"  Sess 1 WM + Ctx: {s1_wm + s1_ctx} mm3 (WM: {s1_wm}, Ctx: {s1_ctx})")
print(f"  Sess 2 WM + Ctx: {s2_wm + s2_ctx} mm3 (WM: {s2_wm}, Ctx: {s2_ctx})")
print(f"  Difference in sum: {((s1_wm + s1_ctx) - (s2_wm + s2_ctx))/1000.0} cm3")

