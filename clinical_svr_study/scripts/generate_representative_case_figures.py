#!/usr/bin/env python3
"""Generate representative MRI/SVR case figures for the manuscript.
Uses matplotlib and nilearn for high-quality, brain-cropped rendering.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
import os
import re

import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import nibabel as nib
from nilearn import plotting
from nilearn.image import crop_img


DEFAULT_DATA_ROOT = Path(
    "/home/ajoshi/project2_ajoshi_27/data/clinical_svr_chla_data"
)
DEFAULT_TABLE = Path("outputs/paired_case_table.csv")
DEFAULT_OUTDIR = Path("outputs/figures")

FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


@dataclass(frozen=True)
class FigureCase:
    case_id: int
    label: str


FIGURES: dict[str, dict[str, object]] = {
    "AA": {
        "title": "Figure AA. Concordant abnormal examples",
        "filename": "figure_AA_concordant_abnormal_examples.png",
        "cases": [
            FigureCase(3, "Ventriculomegaly"),
            FigureCase(4, "Callosal agenesis with colpocephaly"),
            FigureCase(24, "Semilobar holoprosencephaly"),
            FigureCase(14, "Arachnoid cyst"),
            FigureCase(17, "Posterior fossa / cerebellar anomaly"),
            FigureCase(11, "Porencephalic injury with ventriculomegaly"),
        ],
    },
    "BB": {
        "title": "Figure BB. Discordant subtle midline examples",
        "filename": "figure_BB_discordant_midline_examples.png",
        "cases": [
            FigureCase(10, "CSP abnormality or limited CSP visibility"),
            FigureCase(19, "CSP leaflet abnormality vs alternate SVR impression"),
        ],
    },
    "CC": {
        "title": "Figure CC. SVR failure and limited structure visibility",
        "filename": "figure_CC_svr_failure_limited_visibility.png",
        "cases": [
            FigureCase(30, "SVR failure / non-diagnostic reconstruction"),
            FigureCase(16, "Limited structure visibility"),
        ],
    },
}


DTYPES = {
    2: "u1",
    4: "i2",
    8: "i4",
    16: "f4",
    64: "f8",
    256: "i1",
    512: "u2",
    768: "u4",
    1024: "i8",
    1280: "u8",
}


def read_font(path: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype(path, size=size)
    except OSError:
        return ImageFont.load_default()


def load_nifti_to_isotropic_ras(path: Path) -> np.ndarray:
    import nibabel as nib
    import nibabel.processing
    img = nib.load(path)
    img = nib.as_closest_canonical(img)
    img_res = nibabel.processing.resample_to_output(img, voxel_sizes=(1.0, 1.0, 1.0))
    return img_res.get_fdata()


def normalize_case_id(case_id: int) -> list[str]:
    stem = f"{case_id:03d}"
    return [f"SVR{stem}", f"Svr{stem}", f"svr{stem}"]


def find_case_dir(root: Path, case_id: int, subdir: str) -> Path:
    parent = root / "svr" / subdir
    for name in normalize_case_id(case_id):
        candidate = parent / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Could not find case {case_id:03d} under {parent}")


def find_svr_volume(root: Path, table_row: dict[str, str]) -> Path:
    svr_rnd_id = int(table_row.get("svr_randomized_id", 0))
    path = root / "svr_aligned_randomized_31" / f"RND_{svr_rnd_id:04d}_SVR_aligned.nii.gz"
    if not path.exists():
        raise FileNotFoundError(f"Missing randomized SVR output: {path}")
    return path


def raw_axis_from_name(path: Path) -> str | None:
    name = path.name.upper()
    if not all(token in name for token in ("BRAIN", "SSH", "TSE")):
        return None
    if "WHOLE_BODY" in name or "MRCP" in name or "DWI" in name:
        return None
    if "COR" in name:
        return "coronal"
    if "SAG" in name:
        return "sagittal"
    if "AX" in name:
        return "axial"
    return None


def sort_key(path: Path) -> tuple[int, int, str]:
    name = path.name.upper()
    match = re.search(r"(\d+)(?=\.NII(?:\.GZ)?$)", name)
    series = int(match.group(1)) if match else 99999
    preferred = 0 if "AXIAL" in name or "COR_" in name or "SAG_" in name else 1
    return preferred, series, name


def find_raw_stacks(root: Path, case_id: int) -> dict[str, Path]:
    case_dir = find_case_dir(root, case_id, "nifti_in")
    grouped: dict[str, list[Path]] = {"axial": [], "coronal": [], "sagittal": []}
    for path in case_dir.glob("*.nii*"):
        axis = raw_axis_from_name(path)
        if axis:
            grouped[axis].append(path)
    return {
        axis: sorted(paths, key=sort_key)[0]
        for axis, paths in grouped.items()
        if paths
    }


def choose_slice(data: np.ndarray, axis: int) -> int:
    if data.ndim != 3:
        return 0

    finite = np.isfinite(data)
    values = data[finite & (data != 0)]
    if values.size == 0:
        return data.shape[axis] // 2

    threshold = np.percentile(values, 10)
    mask = finite & (data > threshold)
    axes = tuple(i for i in range(3) if i != axis)
    scores = mask.sum(axis=axes)

    lo = max(0, int(round(data.shape[axis] * 0.08)))
    hi = min(data.shape[axis], int(round(data.shape[axis] * 0.92)))
    if hi <= lo:
        lo, hi = 0, data.shape[axis]
    local_scores = scores[lo:hi]
    if local_scores.size == 0 or local_scores.max() == 0:
        return data.shape[axis] // 2
    return int(lo + local_scores.argmax())


def extract_slice(data: np.ndarray, plane: str) -> np.ndarray:
    if data.ndim != 3:
        return np.asarray(data)
    if plane == "axial":
        return data[:, :, choose_slice(data, 2)]
    if plane == "coronal":
        return data[:, choose_slice(data, 1), :]
    if plane == "sagittal":
        return data[choose_slice(data, 0), :, :]
    raise ValueError(f"Unknown plane {plane}")


def crop_foreground(slice_2d: np.ndarray) -> np.ndarray:
    arr = np.asarray(slice_2d)
    finite = np.isfinite(arr)
    values = arr[finite & (arr != 0)]
    if values.size < 20:
        return arr

    threshold = np.percentile(values, 5)
    mask = finite & (arr > threshold)
    coords = np.argwhere(mask)
    if coords.size == 0:
        return arr

    y0, x0 = coords.min(axis=0)
    y1, x1 = coords.max(axis=0) + 1
    pad_y = max(4, int((y1 - y0) * 0.08))
    pad_x = max(4, int((x1 - x0) * 0.08))
    y0 = max(0, y0 - pad_y)
    x0 = max(0, x0 - pad_x)
    y1 = min(arr.shape[0], y1 + pad_y)
    x1 = min(arr.shape[1], x1 + pad_x)
    return arr[y0:y1, x0:x1]


def render_slice(slice_2d: np.ndarray, axis: str, size: int) -> Image.Image:
    arr = np.asarray(slice_2d, dtype=np.float32)
    # RAS orientation: (L->R, P->A, I->S)
    arr = np.flipud(arr.T)
    if axis == "sagittal":
        # Sagittal originally has P->A as columns. flipud(T) makes S UP, P on Left. 
        # Standard sagittal usually has Anterior on Left.
        arr = np.fliplr(arr)
    
    arr = crop_foreground(arr)

    finite = np.isfinite(arr)
    values = arr[finite & (arr != 0)]
    if values.size < 20:
        low, high = 0.0, 1.0
    else:
        low, high = np.percentile(values, [1, 99.5])
        if not np.isfinite(low) or not np.isfinite(high) or high <= low:
            low, high = float(values.min()), float(values.max())
    if high <= low:
        high = low + 1.0

    scaled = np.clip((arr - low) / (high - low), 0, 1)
    scaled[~finite] = 0
    image = Image.fromarray((scaled * 255).astype(np.uint8), mode="L").convert("RGB")
    image.thumbnail((size, size), Image.Resampling.LANCZOS)

    canvas = Image.new("RGB", (size, size), "black")
    x = (size - image.width) // 2
    y = (size - image.height) // 2
    canvas.paste(image, (x, y))
    return canvas


def blank_panel(size: int, text: str, font: ImageFont.ImageFont) -> Image.Image:
    panel = Image.new("RGB", (size, size), "#111111")
    draw = ImageDraw.Draw(panel)
    lines = wrap(text, width=18)
    line_h = font.getbbox("Ag")[3] - font.getbbox("Ag")[1] + 5
    total_h = len(lines) * line_h
    y = (size - total_h) // 2
    for line in lines:
        box = draw.textbbox((0, 0), line, font=font)
        draw.text(((size - (box[2] - box[0])) // 2, y), line, fill="#d0d0d0", font=font)
        y += line_h
    return panel


def load_case_table(path: Path) -> dict[int, dict[str, str]]:
    with path.open(newline="") as f:
        rows = csv.DictReader(f)
        return {int(row["case_id"]): row for row in rows}


def row_label(row: dict[str, str], case: FigureCase) -> str:
    raw = row.get("raw_dx", "")
    svr = row.get("svr_dx", "")
    return (
        f"Case {case.case_id:02d}\n"
        f"{case.label}\n"
        f"Raw: {raw}\n"
        f"SVR: {svr}"
    )


def draw_wrapped(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
    fill: str,
    width: int,
    line_spacing: int = 4,
) -> int:
    x, y = xy
    line_height = font.getbbox("Ag")[3] - font.getbbox("Ag")[1] + line_spacing
    for paragraph in text.splitlines():
        for line in wrap(paragraph, width=38) or [""]:
            draw.text((x, y), line, fill=fill, font=font)
            y += line_height
        y += line_spacing
    return y


def render_case_panels(
    data_root: Path,
    case_id: int,
    panel_size: int,
    small_font: ImageFont.ImageFont,
) -> tuple[list[Image.Image], dict[str, str]]:
    raw_paths = find_raw_stacks(data_root, case_id)
    svr_path = find_svr_volume(data_root, case_id)

    panels: list[Image.Image] = []
    manifest: dict[str, str] = {"svr_path": str(svr_path)}

    for axis in ("axial", "coronal", "sagittal"):
        raw_path = raw_paths.get(axis)
        manifest[f"raw_{axis}_path"] = str(raw_path) if raw_path else ""
        if raw_path:
            panels.append(render_slice(extract_slice(load_nifti_to_isotropic_ras(raw_path), axis), axis, panel_size))
        else:
            panels.append(blank_panel(panel_size, f"Missing raw {axis}", small_font))

    svr_data = load_nifti_to_isotropic_ras(svr_path)
    for axis in ("axial", "coronal", "sagittal"):
        panels.append(render_slice(extract_slice(svr_data, axis), axis, panel_size))

    return panels, manifest


def render_figure_nilearn(
    figure_key: str,
    spec: dict[str, object],
    case_table: dict[int, dict[str, str]],
    data_root: Path,
    outdir: Path,
) -> list[dict[str, str]]:
    cases = list(spec["cases"])
    plt.close('all')
    fig = plt.figure(figsize=(16, 2.5 * len(cases) + 0.5))
    fig.patch.set_facecolor('white')
    
    # 1 col for text + 3 cols for Raw + 3 cols for SVR
    gs = GridSpec(len(cases), 7, width_ratios=[1.8, 1, 1, 1, 1, 1, 1], wspace=0.05, hspace=0.05)
    
    fig.suptitle(spec["title"], fontsize=18, fontweight='bold', x=0.02, ha='left')
    
    columns = ["Raw axial", "Raw coronal", "Raw sagittal", "SVR axial", "SVR coronal", "SVR sagittal"]
    for i, col in enumerate(columns):
        ax = fig.add_subplot(gs[0, i+1])
        ax.axis('off')
        ax.set_title(col, fontsize=12, fontweight='bold', pad=2)

    manifest_rows: list[dict[str, str]] = []
    
    # Define mapping from our column logic to nilearn display_mode
    # Raw is matched to what we have (axial, coronal, sagittal). If raw axis matches, display mode is orthogonal to plane if we want a slice...
    # For nilearn: 'z' = axial slice, 'y' = coronal slice, 'x' = sagittal slice
    disps_raw = ["z", "y", "x"]
    disps_svr = ["z", "y", "x"]

    for row_idx, case in enumerate(cases):
        text_ax = fig.add_subplot(gs[row_idx, 0])
        text_ax.axis('off')
        
        row_data = case_table.get(case.case_id, {})
        raw_dx = row_data.get("raw_dx", "")
        svr_dx = row_data.get("svr_dx", "")
        
        label_text = (
            f"Case {case.case_id:02d}\n"
            f"{case.label}\n\n"
            f"Raw: {raw_dx}\n\n"
            f"SVR: {svr_dx}"
        )
        text_ax.text(0, 0.5, label_text, va='center', ha='left', fontsize=10, linespacing=1.2, wrap=True)
        
        raw_paths = find_raw_stacks(data_root, case.case_id)
        svr_path = find_svr_volume(data_root, row_data)
        
        manifest_rows.append({
            "figure": figure_key,
            "case_id": str(case.case_id),
            "svr_path": str(svr_path),
            "raw_axial_path": str(raw_paths.get("axial", "")),
            "raw_coronal_path": str(raw_paths.get("coronal", "")),
            "raw_sagittal_path": str(raw_paths.get("sagittal", "")),
        })

        for c_idx, axis in enumerate(["axial", "coronal", "sagittal"]):
            ax = fig.add_subplot(gs[row_idx, 1 + c_idx])
            raw_p = raw_paths.get(axis)
            if raw_p and raw_p.exists():
                try:
                    img = nib.load(raw_p)
                    img = nib.as_closest_canonical(img)
                    img = crop_img(img)
                    plotting.plot_anat(img, display_mode=disps_raw[c_idx], cut_coords=1, axes=ax, annotate=False, draw_cross=False, black_bg=False, colorbar=False)
                except Exception as e:
                    ax.text(0.5, 0.5, f"Error\n{e}", ha='center', va='center')
                    ax.axis('off')
            else:
                ax.text(0.5, 0.5, "Missing", ha='center', va='center')
                ax.axis('off')

        try:
            svr_img = nib.load(svr_path)
            svr_img = nib.as_closest_canonical(svr_img)
            svr_img_c = crop_img(svr_img)
            for c_idx, disp in enumerate(disps_svr):
                ax = fig.add_subplot(gs[row_idx, 4 + c_idx])
                plotting.plot_anat(svr_img_c, display_mode=disp, cut_coords=1, axes=ax, annotate=False, draw_cross=False, black_bg=False, colorbar=False)
        except Exception as e:
            for c_idx in range(3):
                ax = fig.add_subplot(gs[row_idx, 4 + c_idx])
                ax.text(0.5, 0.5, "Error", ha='center', va='center')
                ax.axis('off')

    plt.tight_layout(rect=[0, 0, 1, 0.98])
    out_path = outdir / spec["filename"]
    plt.savefig(out_path, dpi=300, facecolor='white', bbox_inches='tight')
    print(f"Wrote {out_path}")
    return manifest_rows
    panel_size = 270
    pad = 16
    label_w = 390
    top_h = 108
    row_h = panel_size + 94
    columns = ["Raw axial", "Raw coronal", "Raw sagittal", "SVR axial", "SVR coronal", "SVR sagittal"]
    cases = list(spec["cases"])

    title_font = read_font(FONT_BOLD, 34)
    header_font = read_font(FONT_BOLD, 20)
    label_font = read_font(FONT_REGULAR, 18)
    small_font = read_font(FONT_REGULAR, 17)

    width = label_w + pad + len(columns) * panel_size + (len(columns) - 1) * pad + pad
    height = top_h + len(cases) * row_h + pad
    canvas = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(canvas)

    draw.text((pad, 24), str(spec["title"]), fill="#111111", font=title_font)

    x0 = label_w + pad
    for i, column in enumerate(columns):
        x = x0 + i * (panel_size + pad)
        box = draw.textbbox((0, 0), column, font=header_font)
        draw.text(
            (x + (panel_size - (box[2] - box[0])) // 2, top_h - 35),
            column,
            fill="#222222",
            font=header_font,
        )

    manifest_rows: list[dict[str, str]] = []
    for row_index, case in enumerate(cases):
        y = top_h + row_index * row_h
        draw.line((pad, y - 10, width - pad, y - 10), fill="#d8d8d8", width=1)

        table_row = case_table.get(case.case_id, {})
        draw_wrapped(
            draw,
            (pad, y + 10),
            row_label(table_row, case),
            label_font,
            "#111111",
            label_w - 2 * pad,
        )

        panels, paths = render_case_panels(data_root, case.case_id, panel_size, small_font)
        for col_index, panel in enumerate(panels):
            x = x0 + col_index * (panel_size + pad)
            canvas.paste(panel, (x, y + 10))

        manifest_row = {
            "figure": figure_key,
            "case_id": str(case.case_id),
            "label": case.label,
            "raw_dx": table_row.get("raw_dx", ""),
            "svr_dx": table_row.get("svr_dx", ""),
            "raw_category": table_row.get("raw_category", ""),
            "svr_primary_category": table_row.get("svr_primary_category", ""),
        }
        manifest_row.update(paths)
        manifest_rows.append(manifest_row)

    outpath = outdir / str(spec["filename"])
    canvas.save(outpath, dpi=(300, 300))
    print(f"Wrote {outpath}")
    return manifest_rows


def write_manifest(rows: list[dict[str, str]], path: Path) -> None:
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--paired-table", type=Path, default=DEFAULT_TABLE)
    parser.add_argument("--outdir", type=Path, default=DEFAULT_OUTDIR)
    parser.add_argument(
        "--figures",
        nargs="+",
        default=["AA", "BB", "CC"],
        choices=sorted(FIGURES),
        help="Figure keys to generate.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)
    case_table = load_case_table(args.paired_table)

    manifest_rows: list[dict[str, str]] = []
    for figure_key in args.figures:
        manifest_rows.extend(
            render_figure_nilearn(
                figure_key,
                FIGURES[figure_key],
                case_table,
                args.data_root,
                args.outdir,
            )
        )
    write_manifest(manifest_rows, args.outdir / "representative_case_figure_manifest.csv")


if __name__ == "__main__":
    main()
