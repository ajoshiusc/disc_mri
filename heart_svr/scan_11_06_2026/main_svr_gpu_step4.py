#!/usr/bin/env python3
"""Run Step 4 with svr_gpu, locally or as one Slurm GPU job per cardiac phase.

Reads Step 1's nifti_files/test*/phase_XX/*.nii.gz directly and prepares copies
with the acquired slice axis along z. Uses test*_template/*.pad.dilated.mask.nii.gz
as the volume mask. svr_gpu has no MIRTK intensity-template argument.

Examples (from heart_svr):
  python3 scan_11_06_2026/main_svr_gpu_step4.py --phases 1 --dry-run
  python3 scan_11_06_2026/main_svr_gpu_step4.py --mode local --phases 1
  python3 scan_11_06_2026/main_svr_gpu_step4.py --mode slurm --phases 1

Auto mode submits on the server and runs sequentially on the local machine.
Default output: ACQUISITION_ROOT/outsvr_gpu/test*/phase_XX_allstacks/.
The default slice thickness and output spacing are both 1.5 mm. Use
--resolution 1.0 for a 1 mm output grid on a GPU with more memory.
"""

import argparse
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys


SERVER_REPO = Path("/project2/ajoshi_1183/Projects/svr_gpu")
LOCAL_REPO = Path("/home/ajoshi/Projects/svr_gpu")
ACQUISITION_NAME = "heart_svr_acquisition_11_06_2026"
ACQUISITION_CANDIDATES = (
    Path("/project2/ajoshi_27/data/heart_svr") / ACQUISITION_NAME,
    Path("/home/ajoshi/project2_ajoshi_27/data/heart_svr") / ACQUISITION_NAME,
)


def default_path(candidates, required):
    return next((path for path in candidates if (path / required).exists()), candidates[0])


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--acquisition-root", type=Path,
                        default=default_path(ACQUISITION_CANDIDATES, "nifti_files"))
    parser.add_argument("--svr-repo", type=Path,
                        default=default_path((SERVER_REPO, LOCAL_REPO), "svr_cli.py"))
    parser.add_argument("--python", type=Path, help="Default: SVR_REPO/.venv/bin/python")
    parser.add_argument("--nifti-root", type=Path, help="Default: ACQUISITION_ROOT/nifti_files")
    parser.add_argument("--output-root", type=Path, help="Default: ACQUISITION_ROOT/outsvr_gpu")
    parser.add_argument("--volume-mask", type=Path, help="Override the experiment's padded dilated mask")
    parser.add_argument("--experiment", help="Optional experiment folder name, e.g. test_data_24cm")
    parser.add_argument("--phases", nargs="+", type=int, help="Phase numbers, e.g. --phases 1 2 23; default: all")
    parser.add_argument("--mode", choices=("auto", "local", "slurm"), default="auto")
    parser.add_argument("--device", type=int, default=0, help="CUDA device visible within the process (default: 0)")
    parser.add_argument("--resolution", type=float, default=1.5,
                        help="Output spacing in mm (default: 1.5 for 6 GB GPUs; use 1.0 with more GPU memory)")
    parser.add_argument("--slice-thickness", type=float, default=1.5, help="Slice thickness in mm (default: 1.5)")
    parser.add_argument("--partition", default="gpu")
    parser.add_argument("--account", default="ajoshi_27")
    parser.add_argument("--cpus", type=int, default=8)
    parser.add_argument("--mem", default="64G")
    parser.add_argument("--time", default="12:00:00")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without writing files or running/submitting jobs")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.resolution <= 0 or args.slice_thickness <= 0 or args.device < 0 or args.cpus < 1:
        parser.error("Resolution, slice thickness and CPU count must be positive; device must be nonnegative")
    if args.phases is not None and any(phase < 1 for phase in args.phases):
        parser.error("Phase numbers must be positive")
    args.acquisition_root = args.acquisition_root.expanduser().resolve()
    args.svr_repo = args.svr_repo.expanduser().resolve()
    args.python = (args.python or args.svr_repo / ".venv/bin/python").expanduser().absolute()
    args.nifti_root = (args.nifti_root or args.acquisition_root / "nifti_files").expanduser().resolve()
    args.output_root = (args.output_root or args.acquisition_root / "outsvr_gpu").expanduser().resolve()
    if args.volume_mask:
        args.volume_mask = args.volume_mask.expanduser().resolve()
    if args.mode == "auto":
        args.mode = "slurm" if args.svr_repo == SERVER_REPO else "local"
    return args


def discover_jobs(args):
    if not (args.svr_repo / "svr_cli.py").is_file():
        raise FileNotFoundError(f"svr_cli.py not found in {args.svr_repo}; set --svr-repo")
    if not args.python.is_file() or not os.access(args.python, os.X_OK):
        raise FileNotFoundError(f"Python environment not found/executable: {args.python}; set --python")
    experiments = sorted(path for path in args.nifti_root.glob("test*") if path.is_dir())
    if args.experiment:
        experiments = [path for path in experiments if path.name == args.experiment]
    if not experiments:
        raise FileNotFoundError(f"No matching test* experiment directories under {args.nifti_root}")
    jobs = []
    for experiment in experiments:
        phases = {int(match.group(1)): path for path in experiment.iterdir()
                  if path.is_dir() and (match := re.fullmatch(r"phase_(\d+)", path.name))}
        selection = sorted(set(args.phases) if args.phases else phases)
        if not selection:
            raise FileNotFoundError(f"No original phase_XX folders under {experiment}")
        missing = set(selection) - phases.keys()
        if missing:
            raise FileNotFoundError(f"Missing phases under {experiment}: {sorted(missing)}")
        for number in selection:
            phase = phases[number]
            stacks = sorted(phase.glob("*.nii.gz"))
            if not stacks:
                raise FileNotFoundError(f"No NIfTI stacks in {phase}")
            if len(stacks) < 2:
                print(f"Skipping {experiment.name}/{phase.name}: only {len(stacks)} stack; at least 2 required.")
                continue
            masks = ([args.volume_mask] if args.volume_mask else sorted(
                (args.acquisition_root / f"{experiment.name}_template").glob("*.pad.dilated.mask.nii.gz")))
            if len(masks) != 1 or not masks[0].is_file():
                raise FileNotFoundError(f"Expected one padded dilated mask for {experiment.name}; found {masks}. Set --volume-mask")
            output = (args.output_root / experiment.name / f"phase_{number:02d}_allstacks" /
                      f"svr_heart_{experiment.name}_phase_{number:02d}_res_{args.resolution:.1f}.nii.gz")
            if output.exists():
                metadata = output.parent / "run.json"
                if not metadata.is_file() or json.loads(metadata.read_text()).get("status") != "complete":
                    raise FileExistsError(
                        f"Output exists without a completed run: {output}. Inspect it or select a new --output-root."
                    )
                print(f"Skipping completed output: {output}")
                continue
            jobs.append(dict(experiment=experiment.name, phase=number, stacks=stacks, mask=masks[0], output=output))
    return jobs


def prepare_stacks(stacks, output_dir):
    """Keep all source pixels; permute the unique shortest acquisition axis to z."""
    import nibabel as nib
    import numpy as np

    output_dir.mkdir(parents=True, exist_ok=True)
    paths, geometry = [], []
    for index, source in enumerate(stacks, 1):
        image = nib.load(source)
        if len(image.shape) != 3:
            raise ValueError(f"Expected a 3D stack: {source} ({image.shape})")
        axis = int(np.argmin(image.shape))
        if list(image.shape).count(image.shape[axis]) != 1:
            raise ValueError(f"Cannot identify a unique acquired slice axis in {source}: {image.shape}")
        order = [i for i in range(3) if i != axis] + [axis]
        # Row i specifies the destination axis for source axis i.
        orientation = np.array([[order.index(i), 1] for i in range(3)])
        prepared = image.as_reoriented(orientation)
        target = output_dir / f"stack_{index:02d}_slices_z.nii.gz"
        nib.save(prepared, target)
        paths.append(target)
        geometry.append(dict(source=str(source), source_shape=list(image.shape),
                             permutation=order, output_shape=list(prepared.shape),
                             spacing_mm=[float(x) for x in prepared.header.get_zooms()]))
    return paths, geometry


def cli_command(args, job, prepared):
    return [str(args.python), str(args.svr_repo / "svr_cli.py"),
            "--input-stacks", *map(str, prepared), "--output", str(job["output"]),
            "--device", str(args.device), "--output-resolution", str(args.resolution),
            "--thicknesses", *([str(args.slice_thickness)] * len(prepared)),
            "--volume-mask", str(job["mask"]), "--segmentation", "none",
            "--registration", "none", "--no-auto-reorient"]


def check_gpu(args):
    code = ("import torch; "
            f"assert torch.cuda.is_available() and torch.cuda.device_count() > {args.device}, "
            "'Requested CUDA GPU is unavailable'; "
            f"print(torch.cuda.get_device_name({args.device}))")
    result = subprocess.run([str(args.python), "-c", code], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError("CUDA is unavailable in the svr_gpu environment; run on an allocated GPU.\n" + result.stderr)
    print(f"GPU: {result.stdout.strip()}", flush=True)


def run_phase(args, job):
    check_gpu(args)
    output_dir = job["output"].parent
    prepared, geometry = prepare_stacks(job["stacks"], output_dir / "prepared_stacks")
    command = cli_command(args, job, prepared)
    manifest = dict(experiment=job["experiment"], phase=job["phase"],
                    mask=str(job["mask"]), output=str(job["output"]),
                    thickness_mm=args.slice_thickness, output_resolution_mm=args.resolution,
                    command=command, stacks=geometry,
                    status="running")
    metadata = output_dir / "run.json"
    metadata.write_text(json.dumps(manifest, indent=2) + "\n")
    log_path = output_dir / "svr_gpu.log"
    print(f"Running {job['experiment']}/phase_{job['phase']:02d}; log: {log_path}", flush=True)
    environment = os.environ.copy()
    environment["SVR_TEMP_DIR"] = str(output_dir / "solver_work")
    environment.setdefault("OMP_NUM_THREADS", str(args.cpus))
    with log_path.open("w") as log:
        log.write("COMMAND: " + shlex.join(command) + "\n\n")
        log.flush()
        result = subprocess.run(command, cwd=args.svr_repo, env=environment,
                                stdout=log, stderr=subprocess.STDOUT)
    manifest["returncode"] = result.returncode
    manifest["status"] = "complete" if result.returncode == 0 and job["output"].is_file() else "failed"
    metadata.write_text(json.dumps(manifest, indent=2) + "\n")
    if manifest["status"] != "complete":
        tail = "\n".join(log_path.read_text(errors="replace").splitlines()[-24:])
        hint = ("\nGPU memory exhausted. Increase --resolution (for example, 2.0 mm) "
                "or use a GPU with more memory. Slice thickness is a separate setting."
                if "out of memory" in tail.lower() else "")
        raise RuntimeError(f"SVR-GPU failed for phase {job['phase']:02d}; see {log_path}\n{tail}{hint}")
    print(f"Created {job['output']}", flush=True)


def worker_command(args, job):
    return [str(args.python), str(Path(__file__).resolve()), "--worker", "--mode", "local",
            "--acquisition-root", str(args.acquisition_root), "--svr-repo", str(args.svr_repo),
            "--python", str(args.python), "--nifti-root", str(args.nifti_root),
            "--output-root", str(args.output_root), "--volume-mask", str(job["mask"]),
            "--experiment", job["experiment"], "--phases", str(job["phase"]),
            "--device", str(args.device), "--resolution", str(args.resolution),
            "--slice-thickness", str(args.slice_thickness)]


def main(argv=None):
    args = parse_args(argv)
    jobs = discover_jobs(args)
    if args.worker:
        if len(jobs) > 1:
            raise ValueError("A worker must handle exactly one phase")
        for job in jobs:
            run_phase(args, job)
        return
    for job in jobs:
        command = worker_command(args, job)
        if args.mode == "slurm":
            command = ["sbatch", "--parsable", "--nodes=1", "--ntasks=1", "--gres=gpu:1",
                       f"--partition={args.partition}", f"--account={args.account}",
                       f"--cpus-per-task={args.cpus}", f"--mem={args.mem}", f"--time={args.time}",
                       f"--job-name=heart-svr-gpu-{job['phase']:02d}",
                       f"--output={job['output'].parent / 'slurm-%j.log'}",
                       "--wrap", f"export OMP_NUM_THREADS={args.cpus}; exec " + shlex.join(command)]
        print(shlex.join(command), flush=True)
        if args.dry_run:
            continue
        if args.mode == "slurm":
            job["output"].parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(command)
        if result.returncode:
            action = "Slurm submission" if args.mode == "slurm" else "SVR-GPU worker"
            raise RuntimeError(
                f"{action} failed for {job['experiment']}/phase_{job['phase']:02d} "
                f"(exit {result.returncode}); see the error above."
            )
    action = "planned" if args.dry_run else ("submitted" if args.mode == "slurm" else "completed")
    print(f"{len(jobs)} phase(s) {action} using {args.mode} mode.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
