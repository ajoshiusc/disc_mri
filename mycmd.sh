#!/bin/bash

#SBATCH --account=ajoshi_27
#SBATCH --partition=epyc-64
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=0:50:00

#module purge
#singularity exec --bind $PWD,/project2/ajoshi_27 /scratch1/ajoshi/svrtk_latest.sif Rscript script.R
module load apptainer
echo $@
eval $@

