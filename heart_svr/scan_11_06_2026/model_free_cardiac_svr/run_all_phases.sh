#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="/home/ajoshi/Projects/svr_gpu/.venv/bin/python"
INPUT_DIR="/home/ajoshi/project2_ajoshi_27/data/heart_svr/heart_svr_acquisition_11_06_2026/test_data_24cm"
SVR_REPO="/home/ajoshi/Projects/svr_gpu"
OUTPUT_DIR="${1:-$SCRIPT_DIR/results_all_phases}"

exec "$PYTHON" "$SCRIPT_DIR/reconstruct_cardiac.py" \
  --input "$INPUT_DIR" \
  --repo "$SVR_REPO" \
  --mask "$SCRIPT_DIR/reference_thoracic_mask.nii.gz" \
  --output "$OUTPUT_DIR" \
  --phases $(seq 1 26) \
  --resolution 1.5 \
  --mode bounded \
  --motion-mm 3 \
  --motion-deg 3 \
  --regularization 0.08 \
  --outer 2 \
  --finalize
