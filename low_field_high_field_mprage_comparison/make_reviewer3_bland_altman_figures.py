from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


OUT_DIR = Path("justin_magma_comparison/Main")
BRAINSUITE_ROI_LIST = Path(
    "/home/ajoshi/Software/BrainSuite23a/svreg/BrainSuiteAtlas1/roi_list_svreg.txt"
)
FREESURFER_LUT = Path("/home/ajoshi/Software/freesurfer_u22/FreeSurferColorLUT.txt")
OUTLIER_THRESHOLD = 0.10
FIG_SIZE = (8.2, 6.4)


@dataclass
class VolumeData:
    name: str
    labels: np.ndarray
    label_names: dict[int, str]
    vols_055t: np.ndarray
    vols_3t: np.ndarray


@dataclass
class ThicknessData:
    name: str
    labels: np.ndarray
    label_names: dict[int, str]
    thickness_055t: np.ndarray
    thickness_3t: np.ndarray


@dataclass
class OutlierSummary:
    figure: str
    panel: str
    software: str
    comparison: str
    label_id: int
    region: str
    mean_abs_percent: float
    max_abs_percent: float
    n_subject_points_over_10pct: int


def read_brainsuite_labels() -> dict[int, str]:
    labels: dict[int, str] = {}
    for line in BRAINSUITE_ROI_LIST.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) == 2:
            labels[int(float(parts[0]))] = parts[1]
    return labels


def read_freesurfer_labels() -> dict[int, str]:
    labels: dict[int, str] = {}
    for line in FREESURFER_LUT.read_text(errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) >= 2 and parts[0].lstrip("-").isdigit():
            labels[int(parts[0])] = parts[1]
    return labels


def load_volume_data() -> tuple[VolumeData, VolumeData]:
    bs_3t = np.load("brainSuite_3T.npz")
    bs_lf = np.load("brainSuite_low_field.npz")
    fs_3t = np.load("freesurfer_3T.npz")
    fs_lf = np.load("freesurfer_low_field.npz")

    brainsuite = VolumeData(
        name="BrainSuite",
        labels=bs_3t["label_ids"].astype(int)[1:-1],
        label_names=read_brainsuite_labels(),
        vols_055t=bs_lf["roi_vols"][:, :, 0, 1:-1] / 1000.0,
        vols_3t=bs_3t["roi_vols"][:, :, 1:-1] / 1000.0,
    )

    freesurfer = VolumeData(
        name="FreeSurfer",
        labels=fs_3t["label_ids"].astype(int)[1:-1],
        label_names=read_freesurfer_labels(),
        vols_055t=fs_lf["roi_vols"][:, :, 0, 1:-1] / 1000.0,
        vols_3t=fs_3t["roi_vols"][:, :, 1:-1] / 1000.0,
    )

    return brainsuite, freesurfer


def load_thickness_data() -> tuple[ThicknessData, ThicknessData]:
    bs_3t = np.load("brainSuite_3T.npz")
    bs_lf = np.load("brainSuite_low_field.npz")
    fs_3t = np.load("freesurfer_3T.npz")
    fs_lf = np.load("freesurfer_low_field.npz")

    fs_cortical_label_ids = fs_3t["cortical_label_ids"].astype(int)
    fs_surface_labels = np.concatenate(
        (1000 + fs_cortical_label_ids, 2000 + fs_cortical_label_ids)
    )

    brainsuite = ThicknessData(
        name="BrainSuite",
        labels=bs_3t["cortical_label_ids"].astype(int),
        label_names=read_brainsuite_labels(),
        thickness_055t=bs_lf["roi_thickness_lf"][:, :, 0, :],
        thickness_3t=bs_3t["roi_thickness_3t"],
    )

    freesurfer = ThicknessData(
        name="FreeSurfer",
        labels=fs_surface_labels,
        label_names=read_freesurfer_labels(),
        thickness_055t=np.concatenate(
            (
                fs_lf["left_roi_thickness_lf"][:, :, 0, :],
                fs_lf["right_roi_thickness_lf"][:, :, 0, :],
            ),
            axis=2,
        ),
        thickness_3t=np.concatenate(
            (fs_3t["left_roi_thickness_3t"], fs_3t["right_roi_thickness_3t"]),
            axis=2,
        ),
    )

    return brainsuite, freesurfer


def bland_altman_stats(diff: np.ndarray) -> tuple[float, float, float, float]:
    bias = float(np.mean(diff))
    sd = float(np.std(diff, ddof=1))
    lower = bias - 1.96 * sd
    upper = bias + 1.96 * sd
    return bias, sd, lower, upper


def short_region_name(name: str) -> str:
    replacements = {
        "Left-": "L ",
        "Right-": "R ",
        "ctx-lh-": "L ctx ",
        "ctx-rh-": "R ctx ",
        "Cerebellum": "Cereb",
        "White-Matter": "WM",
        "White Matter": "WM",
        "hypointensities": "hypoint.",
        "orbito-frontal": "OFG",
        "orbitofrontal": "OFG",
        "parahippocampal": "PHG",
        "subcallosal": "subcall.",
        "superior colliculus": "sup. collic.",
        "lateral geniculate nucleus": "LGN",
        "mamillary body": "mammillary",
        "transvers frontal": "trans. frontal",
        "transverse temporal": "trans. temporal",
        "choroid-plexus": "choroid plex.",
        "Accumbens-area": "accumbens",
        "Inf-Lat-Vent": "inf. lat. vent.",
    }
    shortened = name
    for old, new in replacements.items():
        shortened = shortened.replace(old, new)
    shortened = shortened.replace(" gyrus", "")
    shortened = shortened.replace(" nucleus", "")
    return shortened


def flatten_measure(measure: np.ndarray) -> np.ndarray:
    return measure.reshape(measure.shape[0], -1)


def repeated_labels(labels: np.ndarray, n_subjects: int) -> np.ndarray:
    return np.tile(labels, n_subjects)


def volume_case_arrays(
    data: VolumeData, case: str
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, str, str]:
    n_subjects = data.vols_3t.shape[1]
    labels = repeated_labels(data.labels, n_subjects)

    if case == "055t_repeat":
        x = flatten_measure((data.vols_055t[0] + data.vols_055t[1]) / 2.0)
        diff = flatten_measure(data.vols_055t[0] - data.vols_055t[1])
        comparison = "0.55T test-retest"
        color = "#2563eb"
    elif case == "3t_repeat":
        x = flatten_measure((data.vols_3t[0] + data.vols_3t[1]) / 2.0)
        diff = flatten_measure(data.vols_3t[0] - data.vols_3t[1])
        comparison = "3T test-retest"
        color = "#15803d"
    elif case == "055t_vs_3t":
        mean_055t = data.vols_055t.mean(axis=0)
        mean_3t = data.vols_3t.mean(axis=0)
        x = (mean_055t + mean_3t) / 2.0
        diff = mean_055t - mean_3t
        comparison = "0.55T vs 3T"
        color = "#7e22ce"
    else:
        raise ValueError(f"Unknown case: {case}")

    return x.ravel(), diff.ravel(), labels, x, comparison, color


def thickness_case_arrays(
    data: ThicknessData, case: str
) -> tuple[np.ndarray, np.ndarray, str, str]:
    if case == "055t_repeat":
        x = (data.thickness_055t[0] + data.thickness_055t[1]) / 2.0
        diff = data.thickness_055t[0] - data.thickness_055t[1]
        comparison = "0.55T test-retest"
        color = "#2563eb"
    elif case == "3t_repeat":
        x = (data.thickness_3t[0] + data.thickness_3t[1]) / 2.0
        diff = data.thickness_3t[0] - data.thickness_3t[1]
        comparison = "3T test-retest"
        color = "#15803d"
    elif case == "055t_vs_3t":
        mean_055t = data.thickness_055t.mean(axis=0)
        mean_3t = data.thickness_3t.mean(axis=0)
        x = (mean_055t + mean_3t) / 2.0
        diff = mean_055t - mean_3t
        comparison = "0.55T vs 3T"
        color = "#7e22ce"
    else:
        raise ValueError(f"Unknown case: {case}")
    return x.ravel(), diff.ravel(), comparison, color


def region_outliers(
    figure: str,
    panel: str,
    data: VolumeData | ThicknessData,
    comparison: str,
    x_by_subject_region: np.ndarray,
    diff_by_subject_region: np.ndarray,
) -> tuple[set[int], list[OutlierSummary]]:
    summaries: list[OutlierSummary] = []
    rel = np.abs(diff_by_subject_region) / np.maximum(x_by_subject_region, 1e-6)
    mean_rel = rel.mean(axis=0)
    max_rel = rel.max(axis=0)
    outlier_indices = np.flatnonzero(mean_rel > OUTLIER_THRESHOLD)
    outlier_labels: set[int] = set()
    for idx in outlier_indices:
        label_id = int(data.labels[idx])
        outlier_labels.add(label_id)
        summaries.append(
            OutlierSummary(
                figure=figure,
                panel=panel,
                software=data.name,
                comparison=comparison,
                label_id=label_id,
                region=data.label_names.get(label_id, str(label_id)),
                mean_abs_percent=100.0 * float(mean_rel[idx]),
                max_abs_percent=100.0 * float(max_rel[idx]),
                n_subject_points_over_10pct=int(np.sum(rel[:, idx] > OUTLIER_THRESHOLD)),
            )
        )
    return outlier_labels, summaries


def add_stats_box(ax: plt.Axes, diff: np.ndarray, unit: str) -> None:
    bias, sd, lower, upper = bland_altman_stats(diff)
    text = (
        f"Bias +/- SD: {bias:.2f} +/- {sd:.2f} {unit}\n"
        f"LoA: [{lower:.2f}, {upper:.2f}] {unit}"
    )
    ax.text(
        0.03,
        0.97,
        text,
        transform=ax.transAxes,
        va="top",
        ha="left",
        fontsize=9.0,
        bbox=dict(boxstyle="round,pad=0.30", facecolor="white", edgecolor="0.7", alpha=0.92),
    )


def add_reference_lines(ax: plt.Axes, diff: np.ndarray) -> None:
    bias, _sd, lower, upper = bland_altman_stats(diff)
    ax.axhline(bias, color="#dc2626", linestyle="--", linewidth=1.0)
    ax.axhline(lower, color="0.25", linestyle="--", linewidth=0.9)
    ax.axhline(upper, color="0.25", linestyle="--", linewidth=0.9)


def set_symmetric_ylim(ax: plt.Axes, diff: np.ndarray, minimum: float) -> None:
    bias, _sd, lower, upper = bland_altman_stats(diff)
    extent = max(float(np.max(np.abs(diff))), abs(lower), abs(upper), minimum)
    ax.set_ylim(-1.15 * extent, 1.15 * extent)


def mark_outliers(
    ax: plt.Axes,
    x: np.ndarray,
    diff: np.ndarray,
    labels: np.ndarray,
    outlier_labels: set[int],
    measure_label: str,
) -> None:
    if not outlier_labels:
        return

    outlier_mask = np.isin(labels, list(outlier_labels))
    ax.scatter(
        x[outlier_mask],
        diff[outlier_mask],
        s=34,
        facecolors="none",
        edgecolors="#f97316",
        linewidths=1.0,
        zorder=3,
    )


def plot_ba_panel(
    ax: plt.Axes,
    x: np.ndarray,
    diff: np.ndarray,
    color: str,
    title: str,
    xlabel: str,
    ylabel: str,
    unit: str,
    log_x: bool,
    y_minimum: float,
    outlier_annotation: tuple[np.ndarray, set[int], str] | None = None,
) -> None:
    positive = x > 0
    ax.scatter(x[positive], diff[positive], s=14, c=color, alpha=0.58, edgecolors="none")
    add_reference_lines(ax, diff[positive])
    if log_x:
        ax.set_xscale("log")
        xmin = np.min(x[positive]) * 0.65
        xmax = np.max(x[positive]) * 1.45
        ax.set_xlim(max(xmin, 1e-4), xmax)
    set_symmetric_ylim(ax, diff[positive], y_minimum)
    add_stats_box(ax, diff[positive], unit)
    if outlier_annotation is not None:
        labels, outlier_labels, measure_label = outlier_annotation
        mark_outliers(ax, x[positive], diff[positive], labels[positive], outlier_labels, measure_label)
    ax.set_title(title, fontsize=12.5, loc="left")
    ax.set_xlabel(xlabel, fontsize=11.0)
    ax.set_ylabel(ylabel, fontsize=11.0)
    ax.grid(True, color="0.88", linewidth=0.6)
    ax.tick_params(labelsize=10.0)


def save_field_strength_figure(
    volume_data: tuple[VolumeData, VolumeData],
    thickness_data: tuple[ThicknessData, ThicknessData],
) -> list[OutlierSummary]:
    summaries: list[OutlierSummary] = []
    fig, axes = plt.subplots(2, 2, figsize=FIG_SIZE, constrained_layout=True)
    panels = [
        ("a", thickness_data[0], axes[0, 0], "BrainSuite cortical thickness"),
        ("b", thickness_data[1], axes[0, 1], "FreeSurfer cortical thickness"),
    ]

    for panel, data, ax, title in panels:
        x, diff, _comparison, color = thickness_case_arrays(data, "055t_vs_3t")
        plot_ba_panel(
            ax=ax,
            x=x,
            diff=diff,
            color=color,
            title=f"({panel}) {title}",
            xlabel="Mean of 0.55T and 3T thickness (mm)",
            ylabel="0.55T - 3T thickness (mm)",
            unit="mm",
            log_x=False,
            y_minimum=0.25,
        )

    for panel, data, ax, title in [
        ("c", volume_data[0], axes[1, 0], "BrainSuite ROI volume"),
        ("d", volume_data[1], axes[1, 1], "FreeSurfer ROI volume"),
    ]:
        x, diff, labels, x_by_region, comparison, color = volume_case_arrays(data, "055t_vs_3t")
        diff_by_region = (
            data.vols_055t.mean(axis=0) - data.vols_3t.mean(axis=0)
        )
        outlier_labels, panel_summaries = region_outliers(
            "Figure 4", panel, data, comparison, x_by_region, diff_by_region
        )
        summaries.extend(panel_summaries)
        plot_ba_panel(
            ax=ax,
            x=x,
            diff=diff,
            color=color,
            title=f"({panel}) {title}",
            xlabel="Mean of 0.55T and 3T ROI volume (cm$^3$)",
            ylabel="0.55T - 3T volume (cm$^3$)",
            unit="cm$^3$",
            log_x=True,
            y_minimum=1.0,
            outlier_annotation=(labels, outlier_labels, "volume"),
        )

    fig.savefig(OUT_DIR / "Bland_altman_3Tvs0.55T.pdf", bbox_inches="tight")
    plt.close(fig)
    return summaries


def save_volume_retest_figure(volume_data: tuple[VolumeData, VolumeData]) -> list[OutlierSummary]:
    summaries: list[OutlierSummary] = []
    fig, axes = plt.subplots(2, 2, figsize=FIG_SIZE, constrained_layout=True)
    panel_specs = [
        ("a", volume_data[0], "055t_repeat", axes[0, 0], "BrainSuite 0.55T"),
        ("b", volume_data[0], "3t_repeat", axes[0, 1], "BrainSuite 3T"),
        ("c", volume_data[1], "055t_repeat", axes[1, 0], "FreeSurfer 0.55T"),
        ("d", volume_data[1], "3t_repeat", axes[1, 1], "FreeSurfer 3T"),
    ]
    for panel, data, case, ax, title in panel_specs:
        x, diff, labels, x_by_region, comparison, color = volume_case_arrays(data, case)
        if case == "055t_repeat":
            diff_by_region = data.vols_055t[0] - data.vols_055t[1]
        else:
            diff_by_region = data.vols_3t[0] - data.vols_3t[1]
        outlier_labels, panel_summaries = region_outliers(
            "Figure 5", panel, data, comparison, x_by_region, diff_by_region
        )
        summaries.extend(panel_summaries)
        plot_ba_panel(
            ax=ax,
            x=x,
            diff=diff,
            color=color,
            title=f"({panel}) {title}",
            xlabel="Mean test-retest ROI volume (cm$^3$)",
            ylabel="1st - 2nd repetition (cm$^3$)",
            unit="cm$^3$",
            log_x=True,
            y_minimum=1.0,
            outlier_annotation=(labels, outlier_labels, "volume"),
        )

    fig.savefig(OUT_DIR / "bland_altmann_roi_vol_v7.pdf", bbox_inches="tight")
    plt.close(fig)
    return summaries


def save_thickness_retest_figure(thickness_data: tuple[ThicknessData, ThicknessData]) -> None:
    fig, axes = plt.subplots(2, 2, figsize=FIG_SIZE, constrained_layout=True)
    panel_specs = [
        ("a", thickness_data[0], "055t_repeat", axes[0, 0], "BrainSuite 0.55T"),
        ("b", thickness_data[0], "3t_repeat", axes[0, 1], "BrainSuite 3T"),
        ("c", thickness_data[1], "055t_repeat", axes[1, 0], "FreeSurfer 0.55T"),
        ("d", thickness_data[1], "3t_repeat", axes[1, 1], "FreeSurfer 3T"),
    ]
    for panel, data, case, ax, title in panel_specs:
        x, diff, _comparison, color = thickness_case_arrays(data, case)
        plot_ba_panel(
            ax=ax,
            x=x,
            diff=diff,
            color=color,
            title=f"({panel}) {title}",
            xlabel="Mean test-retest cortical thickness (mm)",
            ylabel="1st - 2nd repetition (mm)",
            unit="mm",
            log_x=False,
            y_minimum=0.25,
        )
    fig.savefig(OUT_DIR / "bland_altmann_thickness_v5.pdf", bbox_inches="tight")
    plt.close(fig)


def write_outlier_csv(summaries: list[OutlierSummary]) -> None:
    output = OUT_DIR / "bland_altman_outliers_10pct.csv"
    with output.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(OutlierSummary.__dataclass_fields__))
        writer.writeheader()
        for summary in summaries:
            writer.writerow(summary.__dict__)


def main() -> None:
    plt.rcParams.update(
        {
            "font.size": 11,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "axes.linewidth": 0.8,
        }
    )
    volume_data = load_volume_data()
    thickness_data = load_thickness_data()
    summaries: list[OutlierSummary] = []
    summaries.extend(save_field_strength_figure(volume_data, thickness_data))
    summaries.extend(save_volume_retest_figure(volume_data))
    save_thickness_retest_figure(thickness_data)
    write_outlier_csv(summaries)


if __name__ == "__main__":
    main()
