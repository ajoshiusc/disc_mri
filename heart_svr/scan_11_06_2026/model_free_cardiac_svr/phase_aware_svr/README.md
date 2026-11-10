# Beat-normalized cardiac slice-to-volume reconstruction

This is a second experimental cardiac SVR method, following a negative result from motion-only temporal smoothing. It changes cardiac phase assignment and the observation likelihood. Each target volume is fitted directly to nearby native observations using a narrow Gaussian temporal kernel; images are not pre-averaged.

## Timing evidence and assumptions

The original filename slice/frame counters recover an order in which trigger times are almost monotonic between heartbeat resets. Each spatial slice group has six frames. The code sorts these counters within each stack, detects negative trigger jumps greater than 100 ms, and estimates each completed heartbeat duration as:

    RR = last_trigger_before_reset + median_frame_interval - first_trigger_after_reset

Only complete interior cycles with plausible 450–1400 ms durations, no unexplained backward trigger jumps and no gaps over 60 ms are used by the new method. The first and last partial cycles are excluded. This infers timing from derived DICOMs; it is not a measured ECG reconstruction and its uncertainty is approximately one frame interval. Original acquisition timestamps or ECG remain preferable. Temporal positions are TriggerTime/RR, on a common 26-bin output cycle. There is no assumption of identical heart rates across stacks or beats. Stack-specific median estimated RR values are about 811, 760 and 695 ms.

The supplied phase labels differ from inferred fractions by approximately 0.025 cycle in the median. The previous solver also combines equal phase numbers across stacks with different bin counts (26/24/22). This pilot tests the combined benefit of beat-normalized rebinning and temporal weighting, not either change in isolation.

## Reconstruction

The objective weights each native frame's likelihood by exp(-0.5*(circular_phase_distance_in_output_bins/0.35)^2), truncating the window at +/-0.6 bins. Spatial slice profiles and scanner geometry remain native. Coverage, gain fitting, robust pixel/slice confidence and the normal equations include this temporal weight. Rigid motion fitting is independent per observation, against the target volume using the same cardiac ROI and original NCC optimizer. There is no shared motion-smoothness penalty from the previous experiment.

Other parameters match the reference: 1.5 mm isotropic voxels, 6 mm native slice thickness, binary thoracic support, cardiac fitting ROI radius 55 mm, two outer iterations, three IRLS iterations, 25 CG iterations, spatial regularization 0.08, 35 motion steps with rate 0.08 and bounds of 3 mm/3 degrees. The cache's interpolated image and any previous fitted image/poses are not used.

## Evaluation

The pilot uses output bins 7 and 14 (23% and 50% cycle). Every seventh original six-frame spatial slice group is excluded from ALL training, normalization, gain and motion fitting. Both methods predict exactly the same held-out frames within +/-0.5 output bin of the inferred target time, in their original scanner poses. No registration or gain is fitted to held-out images; held-out stack gains are the median of fitted training-frame gains for that stack. Training intensity normalization is common to both arms and computed from the union of their training observations only. Comparison metrics measure prediction of the held-out groups, not clinical correctness or measured motion error. Because spatial slices are highly overlapping, this is a local interpolation/generalization check, not an independent subject or scan.

The `original_bins` arm uses exactly the requested original phase tag across stacks; `phase_aware` uses the inferred time and kernel. The new method uses more observations (with fractional temporal weights), as intended. This is not an equal-observation-count ablation. Differences should be attributed to the whole proposed pipeline.

## Reproduction

Requires the existing CUDA Python environment and the original full-run native-data caches and manifests. Each cache includes scanner-space native images, masks, geometry and a record of each DICOM path and its intensity normalization. The timing index was generated from all 6,096 DICOM headers during the previous experiment.

```bash
/home/ajoshi/Projects/svr_gpu/.venv/bin/python reconstruct_phase_aware.py \
  --phases 7 14 \
  --timing-index dicom_timing_index.json \
  --output results
```

The image comparison can be regenerated with `python make_report.py` in the same environment after the pilot. `results/comparison.json` records parameters, timing summaries, data splits and metrics; each arm and phase has a NIfTI, fitted poses, source file lists and metrics. `results/timing_map.json` preserves the inferred timing for every source observation. These pilot volumes exclude validation groups and are not full-data replacements for the previously shared reconstructions.

Related primary work: van Amerom et al., *Fetal whole-heart 4D imaging using motion-corrected multi-planar real-time MRI*, 2019, https://pmc.ncbi.nlm.nih.gov/articles/PMC6617816/ . That work separates cardiac synchronization from spatial motion correction and models dynamic slice data against a periodic 4D reconstruction. This implementation is an experimental kernel-weighted 3D target-time approximation, not a reproduction of that full algorithm.

The initial wider-window attempt exceeded GPU memory. The completed pilot uses sigma=0.35 output bin and a +/-0.6-bin window, comparable to the native frame interval. The same narrower defaults are now in the script. Use `--fit-all --methods phase_aware --output full_data` after validation to include all eligible source slice groups. A complete cycle can be requested with `--phases $(seq 1 26)`; targets are reconstructed sequentially. The `--fit-all` results have no held-out metric and must use a separate output directory from the validation results.

## Cardiac-confidence alternative

`reconstruct_cardiac_confidence.py` keeps original phase tags and the exact reference training/test observations and normalization. It adds cardiac-ROI reliability to the original pixel and whole-frame robust weights. For each frame, a robustly weighted NCC is computed inside the 55 mm heart ROI. Within each stack, only frames with worse-than-median cardiac NCC receive a penalty. Its scale is three robust MAD estimates (with a 0.03 floor); confidence is bounded below by 0.1. Frames with insufficient cardiac ROI mass retain confidence 1. The first solve begins with the original weights; cardiac confidence is updated on subsequent IRLS solves. All calculations use training intensities only. This is an EM-like self-consistency heuristic, not a calibrated probability or a cardiac segmentation model.

Run the confidence comparison after the timing pilot has created `results/comparison.json`:

```bash
/home/ajoshi/Projects/svr_gpu/.venv/bin/python reconstruct_cardiac_confidence.py
```

To fit every original-bin frame rather than holding out groups, use:

```bash
/home/ajoshi/Projects/svr_gpu/.venv/bin/python reconstruct_cardiac_confidence.py \
  --fit-all --phases 7 14 --output full_data
```

A `--pilot` argument can point to the pilot's `comparison.json` if it is elsewhere. The pilot supplies solver settings, cache location and reproducible validation calibration. Its fitted images/poses are not used as priors. Outputs are placed in `cardiac_confidence/phase_XX` under the specified output directory.

## Completed results and recommendation

| Method | Phase 7 cardiac RMSE change | Phase 14 cardiac RMSE change |
|---|---:|---:|
| Beat-normalized phase-aware SVR | +2.24% | -1.62% |
| Cardiac ROI confidence | +0.49% | +0.34% |

Changes are relative to the matched original-bin reference; lower is better. The timing method improved held-out cardiac NCC in phase 14 (0.8062 to 0.8133), but reduced it in phase 7 (0.7936 to 0.7837). Cardiac confidence reduced NCC slightly at both targets. These results do not establish a consistent improvement. Keep the existing full-data original reconstruction as the recommended output. No all-26-phase replacement or full-data run was produced. The optional full-data modes are implemented but were not exercised in these experiments. The comparison is exploratory and has no independent ECG or anatomical ground truth.

`comparison.png` compares the timing method; `comparison_cardiac_confidence.png` compares cardiac confidence. `metrics.csv` contains all three arms; `results/summary.json` contains relative changes. Six NIfTIs are included, two targets per arm. The displayed planes are oblique reconstruction-grid planes, not standard anatomical reformats.

The final compact timing pilot used 37 held-out frames for phase 7 and 25 for phase 14. Both methods' manifests were checked for whole-group exclusion and identical test frames. All six NIfTIs were checked for finite nonempty data and 1.5 mm spacing. The driver and analysis scripts passed Python compilation and the reconstruction/analysis paths were run.
