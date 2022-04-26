#!/bin/bash
#$ -m a
#$ -o /wynton/group/capra/projects/modern_human_3Dgenome/stdout/make_genome/launch_eas.o
#$ -e /wynton/group/capra/projects/modern_human_3Dgenome/stdout/make_genome/launch_eas.e
#$ -t 1-504

## the called SLURM script usees an internal array (ARRY) of chromosome names that the slurm array IDs are then used to index
## ARRY=(1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 X)



###### TODO_Erin
echo $SGE_TASK_ID
INDIV=$(awk -v var="$SGE_TASK_ID" 'NR==var' /wynton/group/capra/projects/modern_human_3Dgenome/data/reference/lists/1kg_indivs_eas.txt)
echo $INDIV


qsub -N make.genome_eas.$INDIV -v "INDIV=$INDIV" -l mem_free=80G -t 1-4 -l h_rt=4:00:00 /wynton/group/capra/projects/modern_human_3Dgenome/bin/makeFASTA/make.genome.1KG.indiv.q
qsub -N make.genome_eas.$INDIV -v "INDIV=$INDIV" -l mem_free=40G -t 5-23 -l h_rt=4:00:00 /wynton/group/capra/projects/modern_human_3Dgenome/bin/makeFASTA/make.genome.1KG.indiv.q
#

#
