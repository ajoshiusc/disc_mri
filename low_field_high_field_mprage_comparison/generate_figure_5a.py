from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from make_reviewer3_bland_altman_figures import (
    load_volume_data,
    volume_case_arrays,
    OUT_DIR,
    plot_ba_panel,
)

def main():
    volume_data = load_volume_data()
    brainsuite_data = volume_data[0]
    
    fig, ax = plt.subplots(1, 1, figsize=(4.1, 3.2), constrained_layout=True)
    
    x, diff, labels, x_by_region, comparison, color = volume_case_arrays(brainsuite_data, "055t_repeat")
    
    plot_ba_panel(
        ax=ax,
        x=x,
        diff=diff,
        color=color,
        title="(a) BrainSuite 0.55T",
        xlabel="Mean test-retest ROI volume (cm$^3$)",
        ylabel="1st - 2nd repetition (cm$^3$)",
        unit="cm$^3$",
        log_x=True,
        y_minimum=1.0,
        outlier_annotation=None, # Without outlier labeling
    )
    
    out_file = OUT_DIR / "bland_altman_fig5a_no_outliers.pdf"
    fig.savefig(out_file, bbox_inches="tight")
    print(f"Saved Figure 5a to {out_file}")

if __name__ == "__main__":
    main()
