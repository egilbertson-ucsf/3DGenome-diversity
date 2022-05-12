#!/usr/bin/env python

# Will calculate 3d genome predictions across the genome in sliding 1 Mb windows for one individual
# Input: Takes one string input which is the name of the individual you want to run Akita on (see function find_inFileLoc for details on how this references a path
# Output: Will output two files 3dpreds_[indiv].txt and coverage_[indiv].txt. Each line (in both files) should reference the 1 Mb window
# The 3D preds file will have a vector representation of the "triangle" output matrix for Akita. The coverage file will have details about the genome coverage for that individual
# and the human reference at that location.

import os
import sys
import json
import sonfigparser
import subprocess

os.environ["CUDA_VISIBLE_DEVICES"] = '-1' ### run on CPU

import tensorflow as tf
print(tf.__version__)
if tf.__version__[0] == '1':
    tf.compat.v1.enable_eager_execution()

import numpy as np
np.random.seed(1337)
import pandas as pd
import pysam
import matplotlib.pyplot as plt
from cooltools.lib.numutils import set_diag

from basenji import dataset, dna_io, seqnn
from matplotlib.pyplot import xticks, yticks
from scipy import stats

## loading config
configfile_name = sys.argv[2]

config = configparser.ConfigParser()
config.read(configfile_name)

GENOME_CHUNKS=config["FILE"]["GENOME_CHUNKS"]


### read sys.argv and determine which regions of the genome are considered ###
indiv = sys.argv[1].strip()
print(indiv)
chunks = {}
with open(GENOME_CHUNKS) as f:
    for line in f:
        chunk = line.strip().split("\t")
        chunks[chunk[0]] = [int(x) for x in chunk[1].split(",")]
f.close()

### load params, specify model ###

model_dir = config["PATH"]["MODEL_DIR"]
params_file = model_dir+config["FILE"]["AKITA_PARAMS"]
model_file  = model_dir+config["FILE"]["MODEL"]
with open(params_file) as params_open:
    params = json.load(params_open)
    params_model = params['model']
    params_train = params['train']

seqnn_model = seqnn.SeqNN(params_model)

### restore model ###
seqnn_model.restore(model_file)

### names of targets ###
data_dir =  config["PATH"]["DATA_DIR"]
targets_file = config["FILE"]["TARGETS"]

hic_targets = pd.read_csv(data_dir+targets_file,sep='\t')
hic_file_dict_num = dict(zip(hic_targets['index'].values, hic_targets['file'].values) )
hic_file_dict     = dict(zip(hic_targets['identifier'].values, hic_targets['file'].values) )
hic_num_to_name_dict = dict(zip(hic_targets['index'].values, hic_targets['identifier'].values) )

### read data parameters ###
data_stats_file = data_dir+config["FILE"]["STATS"]
with open(data_stats_file) as data_stats_open:
    data_stats = json.load(data_stats_open)
seq_length = data_stats['seq_length']
target_length = data_stats['target_length']
hic_diags =  data_stats['diagonal_offset']
target_crop = data_stats['crop_bp'] // data_stats['pool_width']
target_length1 = data_stats['seq_length'] // data_stats['pool_width']


target_length1_cropped = target_length1 - 2*target_crop
print('flattened representation length:', target_length)
print('symmetrix matrix size:', '('+str(target_length1_cropped)+','+str(target_length1_cropped)+')')

### find file location for the individuals considered ###

def find_inFileLoc(indiv, chrm):
    pop = indiv.split('_')[0]
    id = indiv.split('_')[3]
    in_file_loc = config["PATH"]["INPUT_FASTA_DIR"]+'/%s/%s/%s_%s_hg38_full.fa' % (pop,indiv,chrm,id)
    return in_file_loc


### Functions to run akita across the genome ###

def runAkitaPreds(seq):
    if len(seq) != 2**20: raise ValueError('len(seq) != seq_length')
    seq_1hot = dna_io.dna_1hot(seq)
    test_pred_from_seq = seqnn_model.model.predict(np.expand_dims(seq_1hot,0))
    return test_pred_from_seq

f_3d = open((config["PATH"]["OUT_PREDS"] + '3dpreds_%s.txt' % indiv),'w')
f_coverage = open((config["PATH"]["OUT_COV"] + 'coverage_%s.txt' % indiv),'w')

for chrm,pos_list in chunks.items():
    print("On chrom = %s" % chrm)
    try:
        in_file_loc_indiv = find_inFileLoc(indiv, chrm)
        print(in_file_loc_indiv)
        indiv_fasta_open = pysam.Fastafile(in_file_loc_indiv)
        #mask_fasta_open = pysam.Fastafile('/gpfs51/dors2/capra_lab/users/rinkerd/projects/3DNeand/data/genomes/masked_hg19_reference/%s_hg19_archaic.masked.fa' % chrm) #for the masked
        #human19_fasta_open = pysam.Fastafile('/dors/capra_lab/data/dna/human/hg19/%s.fa' % chrm)
    except:
        print("Failed on chr: %s:" % chrm)
        continue

    for start_loc in pos_list:
        print("starting predictions on %s" % start_loc)
        try: # some input start locations won't work because when + 1Mb they are past the end of the chromosome stop
            # Fetch the fasta sequence
            indiv_seq = indiv_fasta_open.fetch(chrm, start_loc, start_loc+2**20).upper()
            #masked_seq = mask_fasta_open.fetch(chrm, start_loc, start_loc+2**20).upper() #for the masked
            #human19_seq = human19_fasta_open.fetch(chrm, start_loc, start_loc+2**20).upper()

            # calculate coverage
            indiv_coverage = np.mean([ 0 if s == "N" else 1 for s in indiv_seq])
            #masked_coverage = np.mean([ 0 if s == "N" else 1 for s in masked_seq]) # for the masked

            # check if low coverage and then don't bother with calculating 3d predictions
            if (indiv_coverage != 1):
                lowCoverage=True
                continue
            else:
                lowCoverage=False

            # fill in missing sequence with human ref
            #indiv_fillMissing_seq = "".join([r if m == "N" else r if s == "N" else s for r, m, s in zip(human19_seq, masked_seq, indiv_seq)])
            # run predictions and save only the HFF cell type predictions
            indiv_pred  = runAkitaPreds(indiv_seq)
            indiv_pred_hff = indiv_pred[:,:,0][0]
        except:
            print("FAILED: %s at %s" % (chrm, start_loc))
            continue

        # write output to files
        f_coverage.write("%s\t%s\t%s\n" % (chrm,start_loc,indiv_coverage))
        if not(lowCoverage):
            f_3d.write(chrm + "\t" + str(start_loc) + "\t" + "\t".join([str(x) for x in indiv_pred_hff]) + "\n")
        else:
            f_3d.write(chrm + "\t" + str(start_loc) + "\t" + "NA\n")

f_3d.close()
f_coverage.close()