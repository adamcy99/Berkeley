#!/usr/bin/env python
"""
Mapper to assign a custom partition key based on value.
INPUT:
    word \t relative frequency
OUTPUT:
    partitionKey \t word \t relative-frequency
"""
import numpy as np
import sys
from operator import itemgetter
import os.path

# helper function
def getPartitionsFromFile(fpath='partitions.txt'):
    """
    Args:   partition file path
    Returns:    partition_keys (sorted list of strings)
                partition_values (descending list of floats)
                
    NOTE 1: make sure the partition file gets passed into Hadoop
    """
    # load in the partition values from file
    assert os.path.isfile(fpath), 'ERROR with partition file'
    with open(fpath,'r') as f:
        vals = f.read()
    partition_cuts = sorted([float(v) for v in vals.split(',')], reverse=True)
    
    # use the first N uppercase letters as custom partition keys
    N = len(partition_cuts)
    KEYS = list(map(chr, range(ord('A'), ord('Z')+1)))[:N]
    partition_keys = sorted(KEYS)

    return partition_keys, partition_cuts


# call your helper function to get partition keys & cutpoints
pKeys, pCuts = getPartitionsFromFile()

# process the input line by line
for line in sys.stdin: 
    word, freq = line.split() 
    
    # prepend the approriate partition key 
    for key,cutpoint in zip(pKeys,pCuts):
        if float(freq) > cutpoint:
            print(f"{key}\t{word}\t{freq}") 
            break                                                           



    
    
    
    
