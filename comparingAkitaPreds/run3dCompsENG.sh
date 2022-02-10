#!/bin/bash
#$ -N runAkitaComps
#$ -l h_rt=3:00:00
#$ -l mem_free=300G #80G
#$ -o /wynton/group/capra/projects/modern_human_3Dgenome/stdout/runAkitaComps_%a.out
#$ -t 1


echo "taskid: ${SGE_TASK_ID}"
echo "JOB_NAME: ${JOB_NAME}"

source /wynton/home/capra/egilbertson/envs/akita/bin/activate


indivs=$(awk -v var="$SGE_TASK_ID" 'NR==var' /wynton/group/capra/projects/modern_human_3Dgenome/data/listOfPairwiseComps.txt)

python run3dComparisons.DCR.ENG.py "$indivs" > runAkitaComps_"$SGE_TASK_ID".python.out
