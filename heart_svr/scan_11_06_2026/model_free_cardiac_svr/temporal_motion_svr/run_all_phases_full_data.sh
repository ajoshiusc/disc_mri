#!/usr/bin/env bash
set -euo pipefail
task_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec /home/ajoshi/Projects/svr_gpu/.venv/bin/python -u "$task_dir/reconstruct_all_phases.py" "$@"
