#!/usr/bin/env python3
"""
Step 2 – Apply transforms and extract image quality metrics.

For every SVR volume found for each subject / TE / stack-count combination:
  1. Applies the cached FLIRT transform (from step 1) to align the volume
     to the fetal atlas space.
  2. Computes CR, CNR, SNR-GM, SNR-WM, SSIM, and NMSE against the maximum-
     stack reference image.
  3. Aggregates per-subject metrics with outlier rejection.
  4. Saves the aggregated data to ``final_data.json`` (consumed by step 3)
     and summary text / JSON files.

Prerequisites: run step1_register.py first.
"""

import json
import os
import subprocess

import nibabel as nib
import numpy as np
from tqdm import tqdm

from config import (
    SUBJECTS, SUBJECT_GA, FETAL_ATLAS_DIR, CACHE_DIR, FINAL_DATA_JSON,
    TE_VALUES, OUTLIER_REJECTION_RATE,
    atlas_ga_str, get_subject_files, has_consecutive_stacks,
    get_tissue_mask_for_subject, calculate_ssim_nmse, calculate_tissue_metrics,
)

METRICS = ['cr', 'cnr', 'snr_gm', 'snr_wm', 'ssim', 'nmse']

# Minimum number of subjects required to include a (TE, stack) data point
MIN_SUBJECTS = 1


# ---------------------------------------------------------------------------
# Phase 2a – apply cached transforms and compute per-iteration metrics
# ---------------------------------------------------------------------------

def extract_metrics_for_all_subjects() -> dict:
    """Return raw per-subject/TE/stack metrics before aggregation."""
    all_data: dict = {te: {} for te in TE_VALUES}
    subject_list   = list(SUBJECTS.items())
    n_total        = len(subject_list)

    for subj_idx, (subj_name, (directory, pat_template)) in enumerate(
        tqdm(subject_list, desc="Extract metrics"), start=1
    ):
        ga         = SUBJECT_GA.get(subj_name, 30)
        atlas_path = os.path.join(FETAL_ATLAS_DIR, f"STA{atlas_ga_str(ga)}.nii.gz")
        print(f"\n[{subj_idx}/{n_total}] Subject: {subj_name} (GA={ga})")

        for te in TE_VALUES:
            stack_files = get_subject_files(directory, pat_template, te)
            if not stack_files or not has_consecutive_stacks(stack_files.keys()):
                continue

            ref_aligned_path = os.path.join(CACHE_DIR, f"{subj_name}_te{te}_ref_aligned.nii.gz")
            ref_mat_path     = os.path.join(CACHE_DIR, f"{subj_name}_te{te}_ref.mat")

            if not os.path.exists(ref_aligned_path):
                print(f"  [MISSING] TE {te}: run step1_register.py first")
                continue

            try:
                ref_data    = nib.load(ref_aligned_path).get_fdata()  # type: ignore[attr-defined]
                tissue_mask = get_tissue_mask_for_subject(subj_name)
            except (OSError, RuntimeError, ValueError) as exc:
                print(f"  [ERROR] TE {te}: {exc}")
                continue

            stack_keys = sorted(stack_files.keys())
            print(f"  TE {te}: stacks {stack_keys}, processing {sum(len(v) for v in stack_files.values())} volumes ...")

            for stacks, fpath_list in stack_files.items():
                all_data[te].setdefault(stacks, {})
                all_data[te][stacks].setdefault(
                    subj_name,
                    {m: [] for m in METRICS},
                )
                # Total subjects accumulated for this (te, stacks) bucket so far
                n_subjs_in_bucket = len(all_data[te][stacks])
                print(f"    stacks={stacks:2d}: {len(fpath_list)} combination(s), "
                      f"total subjects in bucket so far: {n_subjs_in_bucket}")

                for fpath in fpath_list:
                    bname       = os.path.basename(fpath).replace(".nii.gz", "")
                    out_aligned = os.path.join(CACHE_DIR,
                                               f"{subj_name}_{bname}_aligned.nii.gz")

                    try:
                        if not os.path.exists(out_aligned):
                            cmd = (f"flirt -in {fpath} -ref {atlas_path} "
                                   f"-out {out_aligned} -applyxfm -init {ref_mat_path}")
                            subprocess.run(cmd, shell=True, check=True,
                                           stdout=subprocess.DEVNULL)

                        img_data = nib.load(out_aligned).get_fdata()  # type: ignore[attr-defined]
                        cr, cnr, s_gm, s_wm = calculate_tissue_metrics(img_data,
                                                                        tissue_mask)
                        ssim, nmse = calculate_ssim_nmse(img_data, ref_data)

                        bucket = all_data[te][stacks][subj_name]
                        bucket['cr'].append(cr)
                        bucket['cnr'].append(cnr)
                        bucket['snr_gm'].append(s_gm)
                        bucket['snr_wm'].append(s_wm)
                        bucket['ssim'].append(ssim)
                        bucket['nmse'].append(nmse)
                    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError):
                        pass

    return all_data


# ---------------------------------------------------------------------------
# Phase 2b – aggregate (outlier rejection → per-subject means)
# ---------------------------------------------------------------------------

def aggregate(all_data: dict) -> dict:
    """Return {te: {stacks: {metric: [per_subject_means]}}}."""
    agg: dict = {te: {} for te in TE_VALUES}

    for te in all_data:
        for s in all_data[te]:
            agg[te][s] = {m: [] for m in METRICS}
            for subj in all_data[te][s]:
                for metric in METRICS:
                    values = all_data[te][s][subj][metric]
                    valid   = [v for v in values if not np.isnan(v)]
                    if not valid:
                        continue
                    n_keep = max(1, int(len(valid) * (1.0 - OUTLIER_REJECTION_RATE)))
                    if metric == 'nmse':
                        filtered = sorted(valid)[:n_keep]        # lower = better
                    else:
                        filtered = sorted(valid, reverse=True)[:n_keep]  # higher = better
                    agg[te][s][metric].append(float(np.nanmean(filtered)))

    return agg


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def save_final_data_json(final_data: dict) -> None:
    """Persist final_data so step3_plot.py can load it without re-computing."""
    serialisable = {
        str(te): {
            str(s): {metric: vals for metric, vals in md.items()}
            for s, md in sd.items()
        }
        for te, sd in final_data.items()
    }
    with open(FINAL_DATA_JSON, "w", encoding="utf-8") as f:
        json.dump(serialisable, f, indent=2)
    print(f"  Saved aggregated data → {FINAL_DATA_JSON}")


def save_all_data_json(all_data: dict) -> None:
    """Persist raw per-subject metrics structure for full traceability."""
    out_path = os.path.join(
        os.path.dirname(FINAL_DATA_JSON),
        "all_data_raw.json",
    )
    serialisable = {
        str(te): {
            str(s): {
                subj: {metric: vals for metric, vals in subj_metrics.items()}
                for subj, subj_metrics in subj_dict.items()
            }
            for s, subj_dict in te_dict.items()
        }
        for te, te_dict in all_data.items()
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(serialisable, f, indent=2)
    print(f"  Saved raw all-data  → {out_path}")


def save_summary_text(final_data: dict) -> None:
    out_path = os.path.join(
        os.path.dirname(FINAL_DATA_JSON),
        "comprehensive_te_analysis_results.txt",
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("COMPREHENSIVE FETAL MRI IMAGE QUALITY ANALYSIS (10 SUBJECT AVERAGE)\n")
        f.write("=" * 60 + "\n\n")
        f.write("Metrics computed for each TE and stack number:\n"
                "- CR: GM/WM signal ratio\n"
                "- CNR: tissue contrast relative to noise\n"
                "- SNR GM/WM: signal-to-noise ratios\n"
                "- SSIM: structural similarity (vs. max stacks)\n"
                "- NMSE: normalised mean-squared error (vs. max stacks)\n\n")

        for te in TE_VALUES:
            f.write(f"TE {te} ms:\n")
            f.write("Stack\tN_subj\tCR(mean±std)\tCNR(mean±std)\tSNR_GM(mean±std)\tSNR_WM(mean±std)\tSSIM(mean±std)\tNMSE(mean±std)\n")
            f.write("-" * 90 + "\n")
            for s in sorted(s for s in final_data[te] if 1 <= s <= 12):
                n_subj = min(
                    len([v for v in final_data[te][s][m] if not np.isnan(v)])
                    for m in METRICS
                )
                if n_subj < MIN_SUBJECTS:
                    continue
                def _mean_std(key, _s=s, _te=te):
                    vals = [v for v in final_data[_te][_s][key] if not np.isnan(v)]
                    mean = np.nanmean(vals) if vals else np.nan
                    std = np.nanstd(vals, ddof=1) if len(vals) > 1 else 0.0
                    return mean, std
                cr_m, cr_s = _mean_std('cr')
                cnr_m, cnr_s = _mean_std('cnr')
                snr_gm_m, snr_gm_s = _mean_std('snr_gm')
                snr_wm_m, snr_wm_s = _mean_std('snr_wm')
                ssim_m, ssim_s = _mean_std('ssim')
                nmse_m, nmse_s = _mean_std('nmse')
                f.write(f"{s}\t{n_subj}\t"
                        f"{cr_m:.3f}±{cr_s:.3f}\t"
                        f"{cnr_m:.3f}±{cnr_s:.3f}\t"
                        f"{snr_gm_m:.3f}±{snr_gm_s:.3f}\t"
                        f"{snr_wm_m:.3f}±{snr_wm_s:.3f}\t"
                        f"{ssim_m:.3f}±{ssim_s:.3f}\t"
                        f"{nmse_m:.2e}±{nmse_s:.2e}\n")
            f.write("\n")
    print(f"  Saved text summary   → {out_path}")


def save_coverage_report(final_data: dict) -> None:
    """Write a per-metric coverage report: how many subjects/stacks per TE."""
    out_path = os.path.join(
        os.path.dirname(FINAL_DATA_JSON),
        "metric_coverage_report.txt",
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("METRIC COVERAGE REPORT\n")
        f.write("(Only stack counts with >= {} subjects are shown)\n".format(MIN_SUBJECTS))
        f.write("=" * 70 + "\n\n")

        for te in TE_VALUES:
            f.write(f"TE {te} ms:\n")
            f.write(f"  {'Metric':<10}  {'Valid stacks (N_subj)':<50}\n")
            f.write("  " + "-" * 60 + "\n")

            for metric in METRICS:
                stack_info = []
                for s in sorted(s for s in final_data[te] if 1 <= s <= 12):
                    n = len([v for v in final_data[te][s][metric] if not np.isnan(v)])
                    if n >= MIN_SUBJECTS:
                        stack_info.append(f"stack={s}(N={n})")

                n_stacks = len(stack_info)
                detail   = ", ".join(stack_info) if stack_info else "none"
                f.write(f"  {metric:<10}  {n_stacks} stack(s): {detail}\n")
            f.write("\n")

        # Summary table: per TE, per metric → (total qualifying stacks, subject range)
        f.write("SUMMARY TABLE\n")
        f.write("=" * 70 + "\n")
        header = f"{'TE':>6}  {'Metric':<10}  {'#Stacks':>8}  {'Min N_subj':>10}  {'Max N_subj':>10}\n"
        f.write(header)
        f.write("-" * 50 + "\n")
        for te in TE_VALUES:
            for metric in METRICS:
                counts = [
                    len([v for v in final_data[te][s][metric] if not np.isnan(v)])
                    for s in sorted(s for s in final_data[te] if 1 <= s <= 12)
                ]
                qualifying = [n for n in counts if n >= MIN_SUBJECTS]
                if qualifying:
                    f.write(f"{te:>6}  {metric:<10}  {len(qualifying):>8}  "
                            f"{min(qualifying):>10}  {max(qualifying):>10}\n")
                else:
                    f.write(f"{te:>6}  {metric:<10}  {'0':>8}  {'—':>10}  {'—':>10}\n")
        f.write("\n")

    print(f"  Saved coverage report → {out_path}")

    # Also print the summary table to stdout
    print("\nMETRIC COVERAGE SUMMARY (stacks with >= {} subjects):".format(MIN_SUBJECTS))
    print(f"  {'TE':>6}  {'Metric':<10}  {'#Stacks':>8}  {'N_subj range'}")
    print("  " + "-" * 45)
    for te in TE_VALUES:
        for metric in METRICS:
            counts = [
                len([v for v in final_data[te][s][metric] if not np.isnan(v)])
                for s in sorted(s for s in final_data[te] if 1 <= s <= 12)
            ]
            qualifying = [n for n in counts if n >= MIN_SUBJECTS]
            if qualifying:
                print(f"  {te:>6}  {metric:<10}  {len(qualifying):>8}  "
                      f"{min(qualifying)}–{max(qualifying)} subjects")
            else:
                print(f"  {te:>6}  {metric:<10}  {'0':>8}  (insufficient data)")


def save_error_bar_json(final_data: dict) -> None:
    out_path = os.path.join(
        os.path.dirname(FINAL_DATA_JSON),
        "real_error_bar_data.json",
    )

    def _stat(vals, ddof=1):
        v = [x for x in vals if not np.isnan(x)]
        if not v:
            return 0.0, 0.0
        return float(np.nanmean(v)), float(np.nanstd(v, ddof=ddof) if len(v) > 1 else 0.0)

    json_data: dict = {}
    for te in TE_VALUES:
        json_data[str(te)] = {}
        for s in sorted(s for s in final_data[te] if 1 <= s <= 12):
            sd = final_data[te][s]
            entry: dict = {}
            for metric in METRICS:
                mean, std = _stat(sd[metric])
                entry[f"{metric}_mean"] = mean
                entry[f"{metric}_std"]  = std
            json_data[str(te)][str(s)] = entry

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)
    print(f"  Saved error-bar data → {out_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("Step 2: Applying transforms and extracting metrics ...")
    all_data   = extract_metrics_for_all_subjects()

    print("Step 2: Aggregating per-subject metrics (outlier rejection) ...")
    final_data = aggregate(all_data)

    # Print subject/stack counts per TE to the console
    print("\nSubject and stack counts per TE (after aggregation):")
    print(f"  {'TE':>6}  {'#Stacks':>8}  {'N_subj per stack (min–max)'}")
    print("  " + "-" * 50)
    for te in TE_VALUES:
        valid_stacks = sorted(s for s in final_data[te] if 1 <= s <= 12)
        if not valid_stacks:
            print(f"  {te:>6}  {'0':>8}  (no data)")
            continue
        counts = [
            min(len([v for v in final_data[te][s][m] if not np.isnan(v)]) for m in METRICS)
            for s in valid_stacks
        ]
        print(f"  {te:>6}  {len(valid_stacks):>8}  "
              f"{min(counts)}–{max(counts)} subjects  "
              f"(stacks {valid_stacks[0]}–{valid_stacks[-1]})")
    print()

    print("Step 2: Saving outputs ...")
    # Save both structures: raw all_data and aggregated final_data.
    save_all_data_json(all_data)
    save_final_data_json(final_data)
    save_summary_text(final_data)
    save_error_bar_json(final_data)
    save_coverage_report(final_data)
    print("Step 2 complete.")


if __name__ == "__main__":
    main()
