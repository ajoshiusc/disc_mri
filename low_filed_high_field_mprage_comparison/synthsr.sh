#/bin/bash
eval "$(conda shell.bash hook)"

conda activate svr

python ~/projects/SynthSR/scripts/predict_command_line.py $1 $2 --cpu

conda deactivate

