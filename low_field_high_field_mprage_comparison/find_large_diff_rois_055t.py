import numpy as np

# A small subset of standard FreeSurfer LUT for the regions that tend to show large differences
FS_LABELS = {
    2: "Left-Cerebral-White-Matter",
    3: "Left-Cerebral-Cortex",
    7: "Left-Cerebellum-White-Matter",
    8: "Left-Cerebellum-Cortex",
    16: "Brain-Stem",
    41: "Right-Cerebral-White-Matter",
    42: "Right-Cerebral-Cortex",
    46: "Right-Cerebellum-White-Matter",
    47: "Right-Cerebellum-Cortex",
}

def main():
    print("Loading data...")
    try:
        roi_vols_lf = np.load("freesurfer_low_field.npz")["roi_vols"]
        label_ids = np.load("freesurfer_3T.npz")["label_ids"]
    except FileNotFoundError as e:
        print(f"Error loading data: {e}")
        return

    # Preprocessing: Remove unnecessary dimensions and 0/2000 labels
    roi_vols_lf = roi_vols_lf[:, :, 0, 1:-1]
    
    num_reps = roi_vols_lf.shape[0]
    num_subjects = roi_vols_lf.shape[1]
    num_rois = roi_vols_lf.shape[2]
    
    # Reshape to flatten subjects and ROIs together (2, num_subjects * num_rois)
    roi_vols_lf_flat = roi_vols_lf.reshape(2, -1)

    # Valid label IDs (excluding 0 and 2000)
    valid_label_ids = label_ids[1:-1]
    # Tile the label IDs so they align with the flattened array
    tiled_label_ids = np.tile(valid_label_ids, num_subjects)

    # Get volumes for 1st and 2nd repetitions
    rep1 = roi_vols_lf_flat[0]
    rep2 = roi_vols_lf_flat[1]

    # Calculate difference in cm^3 (data is in mm^3)
    diff_0_55T = (rep1 - rep2) / 1000.0

    # Define the threshold
    threshold = 5.0

    # Find indices where difference is greater than the threshold
    indices = np.where(np.abs(diff_0_55T) > threshold)[0]

    print(f"\nFound {len(indices)} occurrences where absolute volume difference > {threshold} cm^3 (0.55T scan 1 vs scan 2):\n")
    print(f"{'Subject Index':<15} | {'Label ID':<10} | {'Label Name':<30} | {'Difference (cm^3)':<15}")
    print("-" * 75)

    for idx in indices:
        # Determine which subject this belongs to
        subj_idx = idx // num_rois
        label_id = tiled_label_ids[idx]
        diff_val = diff_0_55T[idx]
        
        label_name = FS_LABELS.get(label_id, "Unknown Label")
        
        print(f"{subj_idx:<15} | {label_id:<10} | {label_name:<30} | {diff_val:>6.2f}")

if __name__ == "__main__":
    main()