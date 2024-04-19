#!/usr/bin/env python
"""
Mapper to assign a custom partition key for TOS.
INPUT:
    word \t relative frequency
OUTPUT:
    partitionKey \t word \t relative-frequency
"""
import numpy as np
import sys
from operator import itemgetter
import os.path

# helper functions
def makeKeyHash(key, num_reducers):
    """
    Mimic the Hadoop string-hash function.
    
    key             the key that will be used for partitioning
    num_reducers    the number of reducers that will be configured
    """
    byteof = lambda char: int(format(ord(char), 'b'), 2)
    current_hash = 0
    for c in key:
        current_hash = (current_hash * 31 + byteof(c))
    return current_hash % num_reducers

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
    partition_keys = sorted(KEYS, key=lambda k: makeKeyHash(k,N))

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



    
    
    
    
