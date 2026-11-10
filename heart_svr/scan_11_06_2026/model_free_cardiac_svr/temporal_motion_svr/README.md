# Acquisition-neighbor motion regularization for cardiac SVR

This experimental pilot compares independent SVR against a new solver that jointly fits slice motion for phases 1, 2 and 3. It keeps phase-specific images and shares only a weak motion prior. It does not average cardiac images over time or impose a rigid model of cardiac contraction.

## Acquisition audit

The 6,096 derived DICOM files have no AcquisitionTime values. Original acquisition timestamps and reliable RR durations cannot be recovered from these exports. CardiacNumberOfImages differs across stacks: 26, 24 and 22. Later phase bins have broad TriggerTime distributions and phases 25–26 only contain stack 1. Therefore phase number alone does not prove synchronization or acquisition adjacency. Original scanner cine timing or a collaborator-provided mapping would be needed for a reliable rebinning of the entire cardiac cycle.

The pilot builds a conservative graph: same stack and ImagePositionPatient (rounded to 0.001 mm), consecutive AcquisitionNumber, and a positive TriggerTime difference of at most 100 ms. These are candidate within-plane acquisition neighbors, not verified absolute scan-time neighbors. It does not bridge trigger resets or connect adjacent spatial planes on the assumption they were acquired consecutively. For phases 1–3 there are 733 observations and 402 edges, of which 373 connect different phase bins. `dicom_timing_index.json` and the result's `motion_edges.json` record the audit and graph.

## New objective

For each frame, estimate scanner-space rigid corrections p=(rx,ry,rz,tx,ty,tz), relative to its original plane. Fit each frame to its OWN phase-specific reconstructed image using the original robust NCC plus Huber objective. Add:

    lambda_temporal * mean_edges( w_ij * mean_components(((p_i-p_j)/[3deg,3deg,3deg,3mm,3mm,3mm])^2) )

Here lambda_temporal=0.05. w_ij is inverse trigger-time separation, normalized to mean 1. A global best iterate is accepted using the complete regularized objective. This lets well-supported frames constrain noisier neighbors, while each frame retains its own six motion parameters. The original independent arm uses the original per-slice motion optimizer and acceptance rule. The temporal arm necessarily accepts motion using its joint objective. The implementation processes gradient contributions one phase at a time to limit GPU memory.

All other settings match: 1.5 mm isotropic grid, original native slice profile, broad binary thoracic support, 55 mm cardiac fitting ROI, 3 mm/3 degree bounds, 2 outer iterations, 3 IRLS iterations, 25 CG iterations, 35 motion steps, motion learning rate 0.08 and spatial regularization 0.08. Motion corrections are only applied during the second outer iteration. Both arms reuse the same first outer solve, with identical initial prior and gain/robust-weight state.

## Validation and outputs

The pilot ALWAYS withholds 10% of native pixels (the original deterministic mask). Both arms use only training pixels for normalization, initialization, reconstruction, gain fitting and motion. It reports cardiac-ROI and whole-mask held-out prediction RMSE and NCC. This interleaved pixel check is not an independent acquisition or an anatomical ground truth. Outputs are validation reconstructions, rather than all-pixel replacements for the previously shared 26-phase results. A more rigorous subsequent experiment would withhold complete repeat frames or acquisition blocks and assess endocardial edges, chamber volumes and temporal consistency.

The driver reads the previously prepared `native_data.npz` and `inputs.json` under the original full run. It does not read any of that run's fitted volumes or poses. If the timing index is unavailable it reads timing tags from the DICOM paths in `inputs.json`.

Run with the existing CUDA environment:

```bash
/home/ajoshi/Projects/svr_gpu/.venv/bin/python reconstruct_temporal.py \
  --phases 1 2 3 \
  --cache /home/ajoshi/project2_ajoshi_27/data/heart_svr/heart_svr_acquisition_11_06_2026/heart_svr_model_free_1p5mm_motion3mm3deg \
  --output results
```

The default output is `results` beside this script. The pilot keeps the selected phases on GPU; memory grows with the phase count. Three phases were chosen for the 6 GB GPU. The script is not a memory-scalable all-26-phase implementation.

The main outputs are `results/independent/phase_XX/reconstruction.nii.gz`, `results/temporal_motion/phase_XX/reconstruction.nii.gz`, motion poses, metrics and `results/comparison.json`. `run.log` contains progress. Further directions include graph motion priors across confirmed real-time acquisition blocks, confidence-adaptive edge weights, and deformation-compensated temporal image regularization after cardiac synchronization has been established.

Related primary research: van Amerom et al., *Fetal whole-heart 4D imaging using motion-corrected multi-planar real-time MRI* (2019), https://pmc.ncbi.nlm.nih.gov/articles/PMC6617816/ . It treats cardiac synchronization and motion correction as separate reconstruction steps; the pilot here is a new, narrower motion-regularization experiment, not an implementation or validated reproduction of that method.

## Pilot result (phases 1–3)

The complete pilot took 616 seconds on an NVIDIA RTX 2060. Neighbor-motion translation RMS fell from 0.929 to 0.695 mm (25%); rotation RMS fell from 1.273 to 0.631 degrees (50%). These are differences in estimated corrections across graph edges, not true-motion errors.

| Phase | Independent cardiac held-out RMSE | Temporal cardiac held-out RMSE | Change |
|---|---:|---:|---:|
| 1 | 0.081529 | 0.081633 | +0.128% |
| 2 | 0.083596 | 0.083778 | +0.217% |
| 3 | 0.086856 | 0.086907 | +0.058% |

Held-out cardiac NCC also fell slightly for each phase. The smoother motion did not improve held-out cardiac prediction. At the displayed views the reconstructions look very similar. This is not evidence of a clinically meaningful difference. Keep the existing 26-phase all-pixel reconstruction as the current result. No all-phase temporal replacement was produced. The two arms are matched validation fits and should be compared with each other rather than directly with a fit using all pixels.

`comparison.png` displays fixed oblique reconstruction-grid planes through the same heart center, with common intensity scaling and cropping. These are grid planes, not standard anatomical sagittal/coronal/axial reformats. `metrics.csv` and `results/comparison.json` hold quantitative results.
