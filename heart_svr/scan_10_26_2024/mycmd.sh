#!/bin/bash

#SBATCH --account=ajoshi_27
#SBATCH --partition=main
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=1:00:00

module purge
#singularity exec --bind $PWD,/project/ajoshi_27 /scratch1/ajoshi/svrtk_latest.sif Rscript script.R
echo $@
eval $@

