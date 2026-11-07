#!/usr/bin/env python3
"""Convert one irregular DICOM stack to an interpolated 3D NIfTI.

The original files are untouched. dcm2niix interpolates unequal slice
positions onto an equidistant grid; duplicate positions cannot all be
represented independently. This is not a motion-corrected reconstruction.

Example:
    python convert_dcm2niix_resampled.py DICOM_STACK OUTPUT.nii.gz
"""

import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile

import nibabel as nib
import numpy as np
import pydicom


def prepare_dicoms(source, destination):
    files = sorted(source.glob("*.dcm"))
    if len(files) < 3:
        raise ValueError(f"Expected at least three DICOM slices in {source}")

    reference = None
    records = []
    for path in files:
        ds = pydicom.dcmread(path)
        if (
            ds.file_meta.TransferSyntaxUID.is_compressed
            or not ds.file_meta.TransferSyntaxUID.is_little_endian
            or (ds.BitsAllocated, ds.BitsStored, ds.HighBit, ds.PixelRepresentation)
            != (16, 16, 15, 0)
            or ds.SamplesPerPixel != 1
            or ds.PhotometricInterpretation != "MONOCHROME2"
            or float(ds.get("RescaleSlope", 1)) != 1
            or float(ds.get("RescaleIntercept", 0)) != 0
        ):
            raise ValueError(f"Unsupported DICOM pixel encoding or scaling: {path}")
        if "PixelPaddingValue" in ds or "PixelPaddingRangeLimit" in ds:
            raise ValueError(f"DICOM pixel padding requires separate handling: {path}")

        orientation = np.asarray(ds.ImageOrientationPatient, dtype=float)
        position = np.asarray(ds.ImagePositionPatient, dtype=float)
        spacing = np.asarray(ds.PixelSpacing, dtype=float)
        if not (np.all(np.isfinite(orientation)) and np.all(np.isfinite(position))
                and np.all(np.isfinite(spacing)) and np.all(spacing > 0)):
            raise ValueError(f"Invalid DICOM geometry: {path}")
        if reference is None:
            reference = ds
            normal = np.cross(orientation[:3], orientation[3:])
            if (
                not np.isclose(np.linalg.norm(orientation[:3]), 1, atol=1e-4, rtol=0)
                or not np.isclose(np.linalg.norm(orientation[3:]), 1, atol=1e-4, rtol=0)
                or not np.isclose(np.linalg.norm(normal), 1, atol=1e-4, rtol=0)
            ):
                raise ValueError(f"Invalid DICOM orientation: {path}")
            normal /= np.linalg.norm(normal)
        elif (
            ds.SeriesInstanceUID != reference.SeriesInstanceUID
            or ds.Rows != reference.Rows
            or ds.Columns != reference.Columns
            or not np.allclose(spacing, reference.PixelSpacing, atol=1e-4, rtol=0)
            or not np.allclose(orientation, reference.ImageOrientationPatient, atol=1e-4, rtol=0)
        ):
            raise ValueError(f"Inconsistent DICOM stack geometry: {path}")

        pixels = ds.pixel_array
        records.append((float(position @ normal), position, pixels))
        signed = pixels.astype(np.int32) - 32768
        extrema = {
            field: int(ds.get(field)) - 32768
            for field in ("SmallestImagePixelValue", "LargestImagePixelValue",
                          "SmallestPixelValueInSeries", "LargestPixelValueInSeries")
            if field in ds
        }
        ds.PixelData = signed.astype("<i2").tobytes()
        ds.PixelRepresentation = 1
        ds.RescaleIntercept = 32768
        for field, value in extrema.items():
            ds.data_element(field).VR = "SS"
            setattr(ds, field, value)
        ds.save_as(destination / path.name)

    records.sort(key=lambda item: item[0])
    positions = np.array([record[1] for record in records])
    offsets = positions - positions[0]
    in_plane = offsets - np.outer(offsets @ normal, normal)
    if np.max(np.linalg.norm(in_plane, axis=1)) > 0.01:
        raise ValueError(f"Slice positions have in-plane shifts in {source}")
    return reference, normal, records


def validate_original(base, reference, normal, records):
    """Verify dcm2niix kept every original slice and its in-plane geometry."""
    count = len(records)
    if base.shape != (reference.Columns, reference.Rows, count):
        raise ValueError(f"Unexpected dcm2niix original volume shape: {base.shape}")
    lps_to_ras = np.array([-1, -1, 1])
    orientation = np.asarray(reference.ImageOrientationPatient, dtype=float)
    expected_x = lps_to_ras * orientation[:3] * float(reference.PixelSpacing[1])
    expected_y = -lps_to_ras * orientation[3:] * float(reference.PixelSpacing[0])
    expected_origin = lps_to_ras * (
        records[0][1] + orientation[3:] * float(reference.PixelSpacing[0]) * (reference.Rows - 1)
    )
    if (
        not np.allclose(base.affine[:3, 0], expected_x, atol=1e-3, rtol=0)
        or not np.allclose(base.affine[:3, 1], expected_y, atol=1e-3, rtol=0)
        or not np.allclose(base.affine[:3, 3], expected_origin, atol=1e-3, rtol=0)
        or np.dot(base.affine[:3, 2], lps_to_ras * normal) <= 0
    ):
        raise ValueError("Unexpected dcm2niix original orientation or position")

    data = np.asarray(base.dataobj)
    i = 0
    while i < count:
        j = i + 1
        while j < count and abs(records[j][0] - records[i][0]) < 0.01:
            j += 1
        unmatched = list(range(i, j))
        for _, _, pixels in records[i:j]:
            expected = pixels.T[:, ::-1]
            matched = next((k for k in unmatched if np.array_equal(data[:, :, k], expected)), None)
            if matched is None:
                raise ValueError(f"dcm2niix original pixel mismatch near slice {i}")
            unmatched.remove(matched)
        i = j


def convert(source, output):
    if not output.name.endswith(".nii.gz"):
        raise ValueError("Output must end in .nii.gz")
    sidecar = Path(str(output) + ".json")
    if output.exists() or sidecar.exists():
        raise FileExistsError(f"Output or sidecar already exists: {output}")

    with tempfile.TemporaryDirectory(prefix="heart-dcm2niix-") as tmp:
        root = Path(tmp)
        input_dir, output_dir = root / "input", root / "output"
        input_dir.mkdir()
        output_dir.mkdir()
        reference, normal, records = prepare_dicoms(source, input_dir)
        result = subprocess.run(
            ["dcm2niix", "-g", "i", "-f", "converted", "-b", "n",
             "-z", "y", "-o", str(output_dir), str(input_dir)],
            text=True, capture_output=True,
        )
        if result.returncode:
            raise RuntimeError(
                f"dcm2niix failed with exit {result.returncode}:\n"
                f"{result.stdout}\n{result.stderr}"
            )
        produced = sorted(path.name for path in output_dir.glob("*.nii.gz"))
        if produced != ["converted.nii.gz", "converted_Eq_1.nii.gz"]:
            raise RuntimeError(f"Unexpected dcm2niix outputs: {produced}")
        base = nib.load(output_dir / "converted.nii.gz")
        resampled = nib.load(output_dir / "converted_Eq_1.nii.gz")
        validate_original(base, reference, normal, records)

        spacing = float(resampled.header.get_zooms()[2])
        affine = base.affine.copy()
        affine[:3, 2] *= spacing / float(base.header.get_zooms()[2])
        if (
            len(resampled.shape) != 3
            or resampled.shape[:2] != base.shape[:2]
            or spacing <= 0
            or not np.allclose(resampled.get_qform(), affine, atol=1e-3, rtol=0)
        ):
            raise ValueError("Unexpected geometry in dcm2niix resampled output")
        if not np.array_equal(np.asarray(base.dataobj)[:, :, 0],
                              np.asarray(resampled.dataobj)[:, :, 0]):
            raise ValueError("Resampled first slice does not match the source")
        header = resampled.header.copy()
        header.set_data_dtype(np.float32)
        corrected = nib.Nifti1Image(np.asarray(resampled.dataobj, dtype=np.float32), affine, header)
        corrected.set_sform(affine, code=1)
        corrected.set_qform(affine, code=1)

        locations = np.array([record[0] for record in records])
        metadata = {
            "source": str(source.resolve()),
            "output": str(output.resolve()),
            "conversion_method": "dcm2niix equidistant-slice interpolation",
            "source_slices": len(records),
            "duplicate_position_pairs": int(np.count_nonzero(np.diff(locations) < 0.01)),
            "source_position_range_mm": float(locations[-1] - locations[0]),
            "output_shape": list(corrected.shape),
            "output_spacing_mm": [float(x) for x in corrected.header.get_zooms()[:3]],
            "affine_ras": affine.tolist(),
            "notes": [
                "Input was temporarily re-encoded as signed 16-bit with an intercept of 32768.",
                "dcm2niix linearly interpolated slice positions; duplicate-position slices "
                "cannot all be preserved independently.",
                "The dcm2niix resampled sform was corrected using the original affine "
                "and resampled spacing, and checked against its qform.",
                "This output is not motion-corrected.",
            ],
            "dcm2niix_stdout": result.stdout.replace(str(root), "<temporary directory>"),
            "dcm2niix_stderr": result.stderr.replace(str(root), "<temporary directory>"),
        }

        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".conversion-", dir=output.parent) as publish:
            temporary_output = Path(publish) / output.name
            temporary_sidecar = Path(publish) / sidecar.name
            nib.save(corrected, temporary_output)
            temporary_sidecar.write_text(json.dumps(metadata, indent=2) + "\n")
            os.link(temporary_output, output)
            try:
                os.link(temporary_sidecar, sidecar)
            except OSError:
                output.unlink()
                raise
    print(f"Created interpolated volume {output} and metadata {sidecar}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Directory containing one DICOM stack")
    parser.add_argument("output", type=Path, help="New .nii.gz output path")
    args = parser.parse_args()
    convert(args.source, args.output)


if __name__ == "__main__":
    main()
