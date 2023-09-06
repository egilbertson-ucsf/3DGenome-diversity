#!/bin/bash
#$ -N retrieve_IDW_private_variants_SMBE
#$ -cwd
#$ -o /wynton/group/capra/projects/modern_human_3Dgenome/stdout/in_silico_mutagenesis/retrieve_variants_IDWs.out
#$ -e /wynton/group/capra/projects/modern_human_3Dgenome/stdout/in_silico_mutagenesis/retrieve_variants_IDWs.err
#$ -l h_rt=24:00:00
#$ -l mem_free=30G

# change directories
cd ../../data/IDWs

# set paths
script_path="../../bin/3_in_silico_mutagenesis/retrieve_private_variants.py"
genotypes_path="../vcfs/one_zero_genotypes.txt"


# echo "SGE_TASK_ID:  ${SGE_TASK_ID}"
# # assign variables using the SGE task ID
# id="107"
# chr="chr20"
# start="41943040"
# end="42991616"
# name="AFR_YRI_female_NA19116"
# echo "id: ${id}"
# echo "chr: ${chr}"
# echo "start: ${start}"
# echo "end: ${end}"


echo "SGE_TASK_ID:  ${SGE_TASK_ID}"
# assign variables using the SGE task ID
id=$(awk -v row=$SGE_TASK_ID 'NR == row {print $1}' idw_mut_params.txt)
chr=$(awk -v row=$SGE_TASK_ID 'NR == row {print $2}' idw_mut_params.txt)
start=$(awk -v row=$SGE_TASK_ID 'NR == row {print $3}' idw_mut_params.txt)
end=$(awk -v row=$SGE_TASK_ID 'NR == row {print $4}' idw_mut_params.txt)
name=$(awk -v row=$SGE_TASK_ID 'NR == row {print $5}' idw_mut_params.txt)
echo "id: ${id}"
echo "chr: ${chr}"
echo "start: ${start}"
echo "end: ${end}"


# run
python3 "$script_path" --genotypes "$genotypes_path" --ids "$id" --out "${name}_${chr}_${start}.tmp" --region $chr $start $end


# concat .tmp files
# for f in *.tmp >> IDW_variants_new.txt
# cd