# Step 4 with svr_gpu

`main_svr_gpu_step4.py` selects these checkouts automatically:

- Server: `/project2/ajoshi_1183/Projects/svr_gpu`
- Local: `/home/ajoshi/Projects/svr_gpu`

It uses `SVR_REPO/.venv/bin/python`. Set `--python /path/to/python` if the
checkout uses another environment. The launcher itself needs only Python's
standard library; image preparation and reconstruction use that environment.

From `heart_svr`, preview phase 01 without writing files or launching work:

```bash
python3 scan_11_06_2026/main_svr_gpu_step4.py --phases 1 --dry-run
```

On the server, submit phase 01 as a Slurm GPU job:

```bash
python3 scan_11_06_2026/main_svr_gpu_step4.py --mode slurm --phases 1
```

Slurm requests one GPU, eight CPU cores, 64 GB RAM, and 12 hours per phase on
partition `gpu`, account `ajoshi_27`. Override these with `--partition`,
`--account`, `--cpus`, `--mem`, and `--time`. Each phase runs independently.
The MIRTK/Apptainer wrapper is not used.

On the local GPU machine, run phase 01 directly:

```bash
python3 scan_11_06_2026/main_svr_gpu_step4.py --mode local --phases 1
```

Omitting `--phases` processes all available phases. Auto mode submits Slurm jobs
when the server checkout is selected and runs sequentially for the local
checkout. Phases with only one stack are skipped. Completed outputs are skipped
on reruns; existing outputs without a completed run record cause an error.

The acquisition root is selected from `/project2/ajoshi_27/data/heart_svr/` or
the local `/home/ajoshi/project2_ajoshi_27/data/heart_svr/` mount, followed by
`heart_svr_acquisition_11_06_2026`. Override with `--acquisition-root`.
Inputs come directly from `nifti_files/test*/phase_XX/*.nii.gz`; this runner
prepares its own copies and does not require Step 2's rotated files. For these
160 × 160 × N acquisitions it moves the unique shortest axis (the acquired
slice axis) to z, preserving voxel values and physical positions. This avoids
the spacing-based axis ambiguity in this oversampled export.

The mask is `ACQUISITION_ROOT/test*_template/*.pad.dilated.mask.nii.gz`.
Use `--volume-mask` to select one explicitly. The GPU CLI uses it through
`--volume-mask`; it does not accept MIRTK's intensity template. Brain
segmentation and learned SVoRT initialization are disabled. The iterative
slice-to-volume registration in the GPU solver remains enabled.

Defaults are a 1.5 mm output grid and 1.5 mm slice thickness. The 1 mm output
grid exhausted the RTX 2060's 6 GB of VRAM on phase 01. The 1.5 mm grid reduces
the number of reconstruction voxels by about 70%. On a larger GPU, select
`--resolution 1.0`. Override thickness separately with `--slice-thickness`.
If another phase exhausts memory, a coarser output grid such as
`--resolution 2.0` further reduces memory use.

Phase 01 completed all five outer iterations (15 solves) on the RTX 2060 with
the 1.5 mm grid and thickness. Validation output and logs are retained under
`results/gpu_memory_validation/test_data_24cm/phase_01_allstacks/`.

Outputs are under `ACQUISITION_ROOT/outsvr_gpu/test*/phase_XX_allstacks/`:

- Reconstructed `.nii.gz` and any additional solver outputs.
- `prepared_stacks/`: copies with the slice axis along z.
- `svr_gpu.log`: the solver command and output.
- `run.json`: source geometry, command, and completion status.
- `slurm-JOBID.log`: the worker's output for submitted jobs.
- `solver_work/`: intermediate solver artifacts, isolated for each phase.

Use `--output-root` to select another output directory. GPU availability is
checked inside the worker so an unavailable GPU causes a clear failure.
