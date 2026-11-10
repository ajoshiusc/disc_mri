# Model-free cardiac slice-to-volume reconstruction

This folder contains the reproducibility code for the all-phase cardiac reconstructions from the 2026-11-06 24 cm heart acquisition.

## Run all 26 phases

From this folder:

```bash
./run_all_phases.sh
```

By default, the results are written to `results_all_phases/` beside the script. An optional first argument selects another output directory:

```bash
./run_all_phases.sh /path/to/results_all_phases
```

The launcher uses `/home/ajoshi/Projects/svr_gpu/.venv/bin/python`, the original DICOM folder at `/home/ajoshi/project2_ajoshi_27/data/heart_svr/heart_svr_acquisition_11_06_2026/test_data_24cm`, and the repo at `/home/ajoshi/Projects/svr_gpu`. If these paths differ on another machine, edit the variables in `run_all_phases.sh`.

Each phase is saved under `results_all_phases/phase_XX/final/` with a reconstruction NIfTI, coverage map, slice poses, and `result.json`. The preparation cache stores source DICOM hashes so later runs can detect changes. Use a fresh output folder if the input DICOMs, mask, or resolution changes.

## Method and acquisition

The script uses the repo's standard `standalone_inlined.svr` acquisition operator and solver. It keeps the native per-slice DICOM positions and orientations, models the reported 6 mm slice thickness, and applies bounded rigid slice corrections focused on a central cardiac ROI. The selected run uses a 1.5 mm isotropic output grid, regularization 0.08, two outer iterations, and motion limits of 3 mm and 3 degrees per component. It does not use SVoRT, brain segmentation, or a learned anatomical prior.

The included `reference_thoracic_mask.nii.gz` is a checked binary thoracic support mask. The template intensities are not used in reconstruction.

The DICOM pixel spacing is 1.5 mm in-plane and the slice thickness is 6 mm. A 1.5 mm output grid is a sampling choice, not a claim of 1.5 mm through-plane resolution. Phases 1–22 have three orientations, phases 23–24 have two, and phases 25–26 have only one. The last two phases are underconstrained in 3D and should be treated as exploratory. Fit diagnostics from a full run are in-sample unless `--validation` is explicitly used.

## Requirements

- CUDA-capable NVIDIA GPU and a working PyTorch CUDA environment.
- Python environment at `/home/ajoshi/Projects/svr_gpu/.venv` with PyTorch, NumPy, SciPy, nibabel, and pydicom installed.
- The `svr_gpu` repository checkout at `/home/ajoshi/Projects/svr_gpu`.
- The original DICOM folder listed above.

`svr_gpu_source_snapshot.tar.gz`, `svr_gpu_source_hashes.json`, and `svr_gpu_git_commit.txt` record the solver source used for the original run. `environment.txt` records the original Python/GPU environment.
