# All-phase temporal-motion cardiac SVR

Run `bash run_all_phases_full_data.sh`. All 26 phases are selected by default.
The command does not package or upload anything. After it finishes, the assistant
can package the 26 final NIfTIs and previews for the collaborator.

Default output:
`/home/ajoshi/Documents/Codex/2026-11-08/i-w/outputs/heart_svr_cardiac/temporal_motion_all_phases`

The original data mount is currently unavailable. The default cache is therefore
the complete local original reconstruction cache at:
`/home/ajoshi/Documents/Codex/2026-11-08/i-w/outputs/heart_svr_cardiac/results_all_phases`
If the original full-run cache on the data mount is available when the script
starts, it is preferred automatically. Use `--cache /path` to choose explicitly.
Native DICOM-decoded values, masks, positions, orientations and thicknesses are
read from these caches. The archived DICOM timing index supplies graph metadata;
the original DICOM files need not be mounted. Input-cache and source hashes are
recorded for reproducibility and enforced on resume.

## Commands

- Run: `bash run_all_phases_full_data.sh`
- Resume an interrupted run: `bash run_all_phases_full_data.sh --resume`
- Input check without CUDA or reconstruction: `bash run_all_phases_full_data.sh --check-only`
- Different destination: `bash run_all_phases_full_data.sh --output /new/output/path`

Keep `reconstruct_all_phases.py`, `reconstruct_temporal.py` and
`dicom_timing_index.json` together. Requires the existing svr_gpu CUDA environment.

## Method

Same temporal-motion objective and settings as the three-phase pilot:
1.5 mm isotropic grid, native 6 mm slice profile, broad thoracic support,
55 mm cardiac motion-fitting ROI, two outer reconstruction iterations, three
IRLS solves per outer iteration, 25 CG iterations, spatial regularization 0.08,
35 motion steps, learning rate 0.08, +/-3 mm and +/-3 degrees motion bounds,
temporal weight 0.05 and maximum positive trigger gap 100 ms.

The graph links observations at the same scanner plane and stack, with consecutive
acquisition counters and increasing trigger times. It does not connect frames
simply because they have adjacent phase labels. No rebinning, brain model, SVoRT,
image averaging, or later experimental cardiac-confidence weighting is included.
Every phase retains its own image. This full-data run includes all pixels inside
the native mask; unlike the earlier pilot, it has no pixel holdout.

Stage 1 computes each first outer solve sequentially and checkpoints its image,
initial prior, gains and robust weights on disk. Stage 2 fits all phase corrections
jointly. The ROI operators retain exactly the pilot's deterministic sampled pixel
positions, avoiding unsampled ROI storage on the GPU. Stage 3 computes the second
outer solve sequentially with the joint poses. This retains all cross-phase graph
edges instead of dividing the optimization into disconnected phase batches.

## Outputs and completion

Each phase produces:
- `phase_XX/final/reconstruction.nii.gz`
- `phase_XX/final/coverage.nii.gz`
- `phase_XX/final/poses.npy`
- `phase_XX/final/result.json`

`run.log` records reconstruction progress. `COMPLETED.json` is written only after
all requested phase outputs finish. `run_config.json` records settings and hashes.
The checkpoint directory and joint-motion files allow resume. Do not change code,
inputs or settings when resuming; a different experiment needs a new output path.

The previous temporal-motion pilot did not consistently outperform independent
heart SVR. This is the user-requested full-cycle extension, not a proven quality
improvement. Late phases have reduced orientation coverage: 23–24 have two groups,
25–26 only one. Fit diagnostics are in-sample, not independent validation.

## Checks performed before delivery

- All 26 native caches/manifests present; 6,096 frames.
- Matching 1.5 mm grids and reported 6 mm slice thickness.
- 4,819 temporal edges, including 4,458 across phase bins.
- Compact ROI sample indices, predictions and motion gradients match the pilot
  implementation in CPU checks on phases 1, 13 and 26.
- Python compilation and preflight passed.

The full CUDA reconstruction was not started; the user will launch it.
