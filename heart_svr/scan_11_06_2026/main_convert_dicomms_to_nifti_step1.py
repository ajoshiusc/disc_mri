#!/usr/bin/env python3
"""Convert test*/phase_*/stack_* to January-style phase folders of NIfTI stacks.

Like January's slice-increment-validation-disabled workflow, this preserves the
acquired pixel planes and represents their positions using average spacing.
It does NOT resample or average repeated positions. A conventional 3D NIfTI
cannot encode the exact irregular slice positions; warnings quantify that
approximation. No JSON reader is required by the existing SVR code.

The export has already separated cardiac phases and stacks. Convert each as a
3D stack directly, bypassing dicom2nifti's automatic 4D grouping, which mistakes
repeated slice positions for new timepoints and fails with MISSING_DICOM_FILES.
"""

import argparse
import os
from pathlib import Path
import tempfile

from dicom2nifti import common
from dicom2nifti.convert_dir import _remove_accents
from dicom2nifti.image_reorientation import reorient_image
import nibabel as nib
import numpy as np
import pydicom


DEFAULT_INPUT = Path(
    "/home/ajoshi/project2_ajoshi_27/data/heart_svr/"
    "heart_svr_acquisition_11_06_2026"
)
scans_dir_top = str(DEFAULT_INPUT)


def read_stack(stack_dir):
    files = sorted(Path(stack_dir).glob("*.dcm"))
    if len(files) < 2:
        raise ValueError(f"Expected at least two DICOM slices in {stack_dir}")
    dicoms = [pydicom.dcmread(path) for path in files]
    reference = dicoms[0]
    orientation = np.asarray(reference.ImageOrientationPatient, dtype=float)
    spacing = np.asarray(reference.PixelSpacing, dtype=float)
    if (
        orientation.shape != (6,)
        or not np.all(np.isfinite(orientation))
        or not np.allclose(orientation.reshape(2, 3) @ orientation.reshape(2, 3).T,
                           np.eye(2), atol=1e-4, rtol=0)
        or spacing.shape != (2,)
        or not np.all(np.isfinite(spacing))
        or np.any(spacing <= 0)
    ):
        raise ValueError(f"Invalid DICOM orientation or pixel spacing in {stack_dir}")
    for path, ds in zip(files, dicoms):
        if (int(ds.get("NumberOfFrames", 1)) != 1 or ds.SamplesPerPixel != 1
                or ds.PhotometricInterpretation != "MONOCHROME2"):
            raise ValueError(f"Expected single-frame grayscale DICOM: {path}")
        if (
            ds.SeriesInstanceUID != reference.SeriesInstanceUID
            or ds.get("FrameOfReferenceUID") != reference.get("FrameOfReferenceUID")
            or ds.Rows != reference.Rows or ds.Columns != reference.Columns
            or not np.allclose(ds.ImageOrientationPatient, orientation, atol=1e-4, rtol=0)
            or not np.allclose(ds.PixelSpacing, spacing, atol=1e-4, rtol=0)
        ):
            raise ValueError(f"Inconsistent DICOM series geometry: {path}")
        position = np.asarray(ds.ImagePositionPatient, dtype=float)
        if position.shape != (3,) or not np.all(np.isfinite(position)):
            raise ValueError(f"Invalid DICOM slice position: {path}")
    # Stable ties retain separate acquisitions at repeated positions.
    dicoms.sort(key=lambda ds: int(ds.get("InstanceNumber", 0)))
    dicoms = common.sort_dicoms(dicoms)
    return dicoms


def output_name(header):
    if "SeriesNumber" in header:
        name = str(header.SeriesNumber)
        for field in ("SeriesDescription", "SequenceName", "ProtocolName"):
            if field in header:
                name += f"_{header.get(field)}"
                break
    else:
        name = str(header.SeriesInstanceUID)
    return _remove_accents(name) + ".nii.gz"


def convert_stack(stack_dir, output_dir, *, strict_geometry=False):
    dicoms = read_stack(stack_dir)
    positions = np.array([ds.ImagePositionPatient for ds in dicoms], dtype=float)
    expected = np.linspace(positions[0], positions[-1], len(positions))
    max_error = float(np.max(np.linalg.norm(positions - expected, axis=1)))
    duplicate_pairs = int(np.count_nonzero(np.linalg.norm(np.diff(positions, axis=0), axis=1) < 0.01))
    if max_error > 0.01 or duplicate_pairs:
        message = (
            f"{stack_dir}: {duplicate_pairs} repeated-position pairs; "
            f"average-spacing position error up to {max_error:.2f} mm. "
            "Retaining all acquired images without resampling using average slice spacing."
        )
        if strict_geometry:
            raise ValueError(message)
        print(f"WARNING: {message}", flush=True)

    # This is dicom2nifti's ordinary 3D conversion branch, with no timepoint
    # inference and no duplicate removal: the exporter already did the grouping.
    data = common.get_volume_pixeldata(dicoms)
    affine, _ = common.create_affine(dicoms)
    image = nib.Nifti1Image(data, affine)
    image.header.set_xyzt_units("mm")
    if "RepetitionTime" in dicoms[0] and "EchoTime" in dicoms[0]:
        common.set_tr_te(image, dicoms[0].RepetitionTime, dicoms[0].EchoTime)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / output_name(dicoms[0])
    with tempfile.TemporaryDirectory(prefix=".conversion-", dir=output_dir) as tmp:
        temporary_output = Path(tmp) / output.name
        # convert_directory() used in January defaults to this same LAS reorientation.
        converted = reorient_image(image, str(temporary_output))
        converted.set_sform(converted.affine, code=1)
        converted.set_qform(converted.affine, code=1)
        converted.header["descrip"] = b"heart_svr: January-style average spacing; no resampling"
        nib.save(converted, temporary_output)
        saved = nib.load(temporary_output)
        if (saved.shape != converted.shape
                or not np.array_equal(np.asarray(saved.dataobj), np.asarray(converted.dataobj))
                or not np.allclose(saved.affine, converted.affine, atol=1e-3, rtol=0)
                or not np.allclose(saved.get_qform(), converted.affine, atol=1e-3, rtol=0)):
            raise ValueError(f"Saved NIfTI failed pixel/geometry verification: {output}")
        if output.exists():
            existing = nib.load(output)
            if (existing.shape != saved.shape
                    or not np.array_equal(np.asarray(existing.dataobj), np.asarray(saved.dataobj))
                    or not np.allclose(existing.affine, saved.affine, atol=1e-3, rtol=0)):
                raise FileExistsError(
                    f"Existing output differs from this conversion: {output}. "
                    "Choose a new --output-root; existing files are not overwritten."
                )
            print(f"Skipping matching existing output: {output}", flush=True)
            return False
        os.link(temporary_output, output)
    print(f"Converted {stack_dir}: {len(dicoms)} slices -> {output}", flush=True)
    return True


def main(scans_dir_top=scans_dir_top, nifti_dir_top=None, *, phases=None, strict_geometry=False):
    input_root = Path(scans_dir_top)
    output_root = Path(nifti_dir_top) if nifti_dir_top is not None else input_root / "nifti_files"
    experiments = sorted(path for path in input_root.glob("test*") if path.is_dir())
    if not experiments:
        raise FileNotFoundError(f"No test* experiment directories in {input_root}")

    converted = skipped = 0
    for experiment in experiments:
        if phases:
            phase_dirs = [experiment / name for name in phases]
            for phase in phase_dirs:
                if phase.parent != experiment or not phase.is_dir():
                    raise ValueError(f"Phase directory not found: {phase}")
        else:
            phase_dirs = sorted(path for path in experiment.glob("phase_*") if path.is_dir())
        if not phase_dirs:
            raise ValueError(f"No phase directories in {experiment}")
        for phase in phase_dirs:
            stacks = sorted(path for path in phase.glob("stack_*") if path.is_dir())
            if not stacks:
                raise ValueError(f"No stack directories in {phase}")
            names = set()
            output_dir = output_root / experiment.name / phase.name
            for stack in stacks:
                files = sorted(stack.glob("*.dcm"))
                if not files:
                    raise ValueError(f"No DICOM slices in {stack}")
                name = output_name(pydicom.dcmread(files[0], stop_before_pixels=True))
                if name in names:
                    raise ValueError(f"Multiple stacks have the same output name in {phase}: {name}")
                names.add(name)
                if convert_stack(stack, output_dir, strict_geometry=strict_geometry):
                    converted += 1
                else:
                    skipped += 1
    print(f"Completed: {converted} stacks converted, {skipped} matching outputs skipped.")
    return converted, skipped


def cli():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-root", type=Path,
                        help="Default: INPUT_ROOT/nifti_files_jan_style; existing files are preserved")
    parser.add_argument("--phases", nargs="+", help="For example: phase_01 phase_16; default: all phases")
    parser.add_argument("--strict-geometry", action="store_true",
                        help="Reject irregular/repeated positions instead of the January-style approximation")
    args = parser.parse_args()
    main(args.input_root, args.output_root, phases=args.phases, strict_geometry=args.strict_geometry)


if __name__ == "__main__":
    cli()
