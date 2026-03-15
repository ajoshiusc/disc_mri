#!/usr/bin/env python3
"""
Step 1 – Compute base FLIRT registrations.

For each subject / TE combination, registers the highest-stack SVR image
to the fetal atlas using a 6-DOF rigid alignment (normmi cost).  The
resulting .mat transform and aligned image are cached in CACHE_DIR so
that step 2 can re-use them without re-running FLIRT.

Run this script once before running step2_extract_metrics.py.
"""

import os
import subprocess
from tqdm import tqdm

from config import (
    SUBJECTS, SUBJECT_GA, FETAL_ATLAS_DIR, CACHE_DIR,
    TE_VALUES, atlas_ga_str, get_subject_files, has_consecutive_stacks,
)


def register_subject_te(subj_name: str, directory: str, pat_template: str, te: int) -> None:
    ga         = SUBJECT_GA.get(subj_name, 30)
    atlas_path = os.path.join(FETAL_ATLAS_DIR, f"STA{atlas_ga_str(ga)}.nii.gz")

    stack_files = get_subject_files(directory, pat_template, te)
    if not stack_files:
        return

    if not has_consecutive_stacks(stack_files.keys()):
        print(f"  [SKIP] {subj_name} TE {te}: stacks {sorted(stack_files.keys())} "
              "are not consecutive with step 1")
        return

    max_stacks = max(stack_files.keys())
    ref_path   = stack_files[max_stacks][0]

    ref_aligned_path = os.path.join(CACHE_DIR, f"{subj_name}_te{te}_ref_aligned.nii.gz")
    ref_mat_path     = os.path.join(CACHE_DIR, f"{subj_name}_te{te}_ref.mat")

    if os.path.exists(ref_aligned_path):
        print(f"  [CACHED] {subj_name} TE {te} – skipping (already registered)")
        return

    print(f"  [FLIRT] Registering {subj_name} TE {te} (max stacks={max_stacks}) ...")
    cmd = (
        f"flirt -in {ref_path} -ref {atlas_path} "
        f"-omat {ref_mat_path} -out {ref_aligned_path} "
        f"-dof 6 -searchrx -180 180 -searchry -180 180 -searchrz -180 180 "
        f"-cost normmi"
    )
    subprocess.run(cmd, shell=True, check=True, stdout=subprocess.DEVNULL)


def main() -> None:
    print("Step 1: Computing all base FLIRT registrations ...")
    for subj_name, (directory, pat_template) in tqdm(SUBJECTS.items(), desc="Subjects"):
        for te in TE_VALUES:
            register_subject_te(subj_name, directory, pat_template, te)
    print("Step 1 complete.  Registration files are cached in:", CACHE_DIR)


if __name__ == "__main__":
    main()
