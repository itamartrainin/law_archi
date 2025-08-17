#! /bin/bash
#SBATCH --mem=50g
#SBATCH -c 8
#SBATCH --time=24:0:0
#SBATCH --mail-user=itamar.trainin@mail.huji.ac.il
#SBATCH --mail-type=BEGIN,END,FAIL,TIME_LIMIT
#SBATCH -o "/cs/labs/oabend/itamar.trainin/slurm/extract_content_%j.txt"

dir=/cs/labs/oabend/itamar.trainin/projects/law_archi
cd $dir

source /cs/labs/oabend/itamar.trainin/venvs/nov2024_2/bin/activate

python3 extract_content.py
