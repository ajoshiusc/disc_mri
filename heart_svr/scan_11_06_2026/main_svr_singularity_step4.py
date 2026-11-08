"""Submit one SVR reconstruction per phase using all available rotated stacks."""

import argparse
from pathlib import Path
import shlex
import subprocess


ACQUISITION_NAME = "heart_svr_acquisition_11_06_2026"
DATA_ROOT_CANDIDATES = (
    Path("/project2/ajoshi_27/data/heart_svr"),
    Path("/home/ajoshi/project2_ajoshi_27/data/heart_svr"),
)
DEFAULT_ACQUISITION = next(
    (root / ACQUISITION_NAME for root in DATA_ROOT_CANDIDATES
     if (root / ACQUISITION_NAME / "nifti_files").is_dir()),
    DATA_ROOT_CANDIDATES[0] / ACQUISITION_NAME,
)
DEFAULT_CONTAINER = Path("/project2/ajoshi_27/svrtk_latest.sif")
DEFAULT_SBATCH_SCRIPT = Path(__file__).with_name("mycmd.sh")
DEFAULT_THICKNESS_MM = 3
DEFAULT_RESOLUTION_MM = 1.0


def find_template(acquisition_root, experiment_name):
    template_dir = acquisition_root / f"{experiment_name}_template"
    templates = sorted(template_dir.glob("p*_*.pad.nii.gz"))
    if len(templates) != 1:
        raise FileNotFoundError(
            f"Expected exactly one padded template in {template_dir}; found {len(templates)}"
        )
    template = templates[0]
    mask = Path(str(template)[:-len(".pad.nii.gz")] + ".pad.dilated.mask.nii.gz")
    if not mask.is_file():
        raise FileNotFoundError(f"Padded dilated mask not found: {mask}")
    return template, mask


def make_container_command(stacks, template, mask, output_dir, output_name,
                           *, container, bind_root, resolution, thickness):
    args = [
        "mirtk", "reconstruct", output_name, str(len(stacks)), *map(str, stacks),
        "--resolution", str(resolution), "--thickness",
        *([str(thickness)] * len(stacks)), "--template", str(template),
        "--mask", str(mask),
    ]
    shell_command = f"cd {shlex.quote(str(output_dir))} && {' '.join(shlex.quote(arg) for arg in args)}"
    return " ".join(shlex.quote(arg) for arg in [
        "apptainer", "run", "--bind", str(bind_root), str(container),
        "/bin/bash", "-lic", shell_command,
    ])


def submit_phase(phase_dir, acquisition_root, output_root, sbatch_script,
                 container=DEFAULT_CONTAINER, bind_root=Path("/project2/ajoshi_27"),
                 resolution=DEFAULT_RESOLUTION_MM, thickness=DEFAULT_THICKNESS_MM):
    stacks = sorted(phase_dir.glob("*.nii.gz"))
    if len(stacks) < 2:
        print(f"Skipping {phase_dir.name}: found {len(stacks)} rotated stack(s); at least 2 are needed for SVR.")
        return False

    experiment_name = phase_dir.parent.name
    template, mask = find_template(acquisition_root, experiment_name)
    phase_number = phase_dir.name[len("phase_"):-len("_rot")]
    output_name = f"svr_heart_{experiment_name}_phase_{phase_number}_res_{resolution:.1f}.nii.gz"
    output_dir = output_root / experiment_name / f"phase_{phase_number}_allstacks"
    output_file = output_dir / output_name
    if output_file.is_file():
        print(f"SVR output already exists, skipping: {output_file}")
        return False

    output_dir.mkdir(parents=True, exist_ok=True)
    container_command = make_container_command(
        stacks, template, mask, output_dir, output_name,
        container=container, bind_root=bind_root,
        resolution=resolution, thickness=thickness,
    )
    result = subprocess.run(
        ["sbatch", str(sbatch_script), container_command],
        check=True, capture_output=True, text=True,
    )
    print(f"Submitted {phase_dir.name} with {len(stacks)} stacks: {result.stdout.strip()}")
    return True


def main(acquisition_root=DEFAULT_ACQUISITION, *, nifti_root=None, output_root=None,
         sbatch_script=DEFAULT_SBATCH_SCRIPT, container=DEFAULT_CONTAINER,
         bind_root=Path("/project2/ajoshi_27"), phases=None):
    acquisition_root = Path(acquisition_root)
    nifti_root = Path(nifti_root) if nifti_root else acquisition_root / "nifti_files"
    output_root = Path(output_root) if output_root else acquisition_root / "outsvr_pad"
    sbatch_script = Path(sbatch_script)
    if not acquisition_root.is_dir():
        raise FileNotFoundError(f"Acquisition directory not found: {acquisition_root}")
    if not sbatch_script.is_file():
        raise FileNotFoundError(f"Slurm wrapper not found: {sbatch_script}")

    experiments = sorted(path for path in nifti_root.glob("test*") if path.is_dir())
    if not experiments:
        raise FileNotFoundError(f"No test* experiment folders under {nifti_root}")

    submitted = skipped = 0
    for experiment in experiments:
        phase_dirs = sorted(
            path for path in experiment.glob("phase_*_rot") if path.is_dir()
        )
        if phases:
            requested = {f"phase_{int(phase):02d}_rot" for phase in phases}
            phase_dirs = [path for path in phase_dirs if path.name in requested]
            missing = requested - {path.name for path in phase_dirs}
            if missing:
                raise FileNotFoundError(f"Rotated phase folders not found under {experiment}: {sorted(missing)}")
        for phase_dir in phase_dirs:
            if submit_phase(
                phase_dir, acquisition_root, output_root, sbatch_script,
                container=container, bind_root=bind_root,
            ):
                submitted += 1
            else:
                skipped += 1
    print(f"Done: submitted {submitted} phase(s), skipped {skipped}.")
    return submitted, skipped


def cli():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--acquisition-root", type=Path, default=DEFAULT_ACQUISITION)
    parser.add_argument("--nifti-root", type=Path,
                        help="Default: ACQUISITION_ROOT/nifti_files")
    parser.add_argument("--output-root", type=Path,
                        help="Default: ACQUISITION_ROOT/outsvr_pad")
    parser.add_argument("--sbatch-script", type=Path, default=DEFAULT_SBATCH_SCRIPT)
    parser.add_argument("--container", type=Path, default=DEFAULT_CONTAINER)
    parser.add_argument("--bind-root", type=Path, default=Path("/project2/ajoshi_27"))
    parser.add_argument("--phases", nargs="+", type=int,
                        help="Optional phase numbers, for example --phases 1 2 23")
    args = parser.parse_args()
    main(
        args.acquisition_root,
        nifti_root=args.nifti_root,
        output_root=args.output_root,
        sbatch_script=args.sbatch_script,
        container=args.container,
        bind_root=args.bind_root,
        phases=args.phases,
    )


if __name__ == "__main__":
    cli()
