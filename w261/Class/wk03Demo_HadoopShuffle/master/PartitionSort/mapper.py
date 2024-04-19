#!/usr/bin/env python
"""
Mapper partitions based on first letter in word.
INPUT:
    word \t count
OUTPUT:
    partitionKey \t word \t count  
"""
import re
import sys
    
def getPartitionKey(word,count):
    """ 
    Helper function to assign partition key ('A', 'B', or 'C').
    Args:  word (str) ; count (int)
    """
    ############ YOUR CODE HERE ##########
    if count > 8:                           # <--- SOLUTION --->
        return  'B'                         # <--- SOLUTION --->
    elif count > 4:                         # <--- SOLUTION --->
        return  'C'                         # <--- SOLUTION --->
    else:                                   # <--- SOLUTION --->
        return 'A'                          # <--- SOLUTION --->
    
    # provided implementation: (run this first, then make your changes in part e)
    if word[0] < 'h': 
        return  'A'
    elif word[0] < 'p':
        return  'B'
    else:
        return 'C'
    ############ (END) YOUR CODE #########
    
# read from standard input
for line in sys.stdin:    
    word, count = line.strip().split()
    count = int(count)
    partitionKey = getPartitionKey(word, count) 
    print(f"{partitionKey}\t{word}\t{count}")