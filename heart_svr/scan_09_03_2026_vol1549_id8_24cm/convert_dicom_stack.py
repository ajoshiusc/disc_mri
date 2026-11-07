#!/usr/bin/env python3
"""Convert one exported heart stack using the existing heart_svr converter.

dicom2nifti is attempted first with the heart_svr slice-increment setting. Some
exported phases contain incomplete TriggerTime groups; for those, SimpleITK's
GDCM series reader provides a 3D fallback and the reason is recorded in JSON.
"""
from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile


def convert(source: Path, output: Path):
    import nibabel as nib

    output.parent.mkdir(parents=True, exist_ok=True)
    fallback_reason = None
    dicom_count = len(list(source.glob('*.dcm')))
    try:
        import dicom2nifti
        import dicom2nifti.settings as settings
        settings.disable_validate_slice_increment()
        with tempfile.TemporaryDirectory(prefix='heart_dcm2nii_') as tmp:
            dcm_stdout, dcm_stderr = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(dcm_stdout), contextlib.redirect_stderr(dcm_stderr):
                dicom2nifti.convert_dir.convert_directory(str(source), tmp, compression=True)
            converted = sorted(Path(tmp).glob('*.nii*'))
            if len(converted) != 1:
                detail = (dcm_stdout.getvalue() + '\n' + dcm_stderr.getvalue()).strip()
                raise RuntimeError(f'dicom2nifti returned {len(converted)} volumes; expected one. {detail[:2000]}')
            shutil.copy2(converted[0], output)
        method = 'dicom2nifti'
    except Exception as exc:
        fallback_reason = f'{type(exc).__name__}: {exc}'
        import SimpleITK as sitk
        series_ids = sitk.ImageSeriesReader.GetGDCMSeriesIDs(str(source))
        if not series_ids:
            raise RuntimeError(f'No DICOM series found in {source}')
        if len(series_ids) != 1:
            raise RuntimeError(f'Expected one DICOM series in {source}; found {len(series_ids)}')
        files = sitk.ImageSeriesReader.GetGDCMSeriesFileNames(str(source), series_ids[0])
        reader = sitk.ImageSeriesReader()
        reader.SetFileNames(files)
        image = reader.Execute()
        sitk.WriteImage(image, str(output), True)
        dicom_count = len(files)
        method = 'SimpleITK-GDCM fallback'

    nii = nib.load(str(output))
    meta = {
        'source': str(source),
        'output': str(output),
        'dicom_count': dicom_count,
        'shape_xyz': list(nii.shape),
        'spacing_mm': [float(x) for x in nii.header.get_zooms()[:3]],
        'affine': nii.affine.tolist(),
        'conversion_method': method,
        'dicom2nifti_fallback_reason': fallback_reason,
    }
    Path(str(output) + '.json').write_text(json.dumps(meta, indent=2) + '\n')
    return meta


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit('usage: convert_dicom_stack.py DICOM_STACK_DIR OUTPUT.nii.gz')
    convert(Path(sys.argv[1]), Path(sys.argv[2]))
