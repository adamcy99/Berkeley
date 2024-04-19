#!/usr/bin/env python
"""
Mapper script to tokenize words from a line of text.
INPUT:
    a text file
OUTPUT:
    word \t partialCount
"""
import re
import sys

def getPartitionKey(word):
    "Helper function to assign partition key alphabetically."
    ############## YOUR CODE HERE ##############
    if word[0] < 'g': 
        return  'A'
    elif word[0] < 'm':
        return  'B'
    elif word[0] < 's':
        return 'C'
    else:
        return 'D'







    ############## (END) YOUR CODE ##############
    
# initialize local aggregator for total word count
TOTAL_WORDS = 0
# read from standard input
for line in sys.stdin:
    line = line.strip()
    # tokenize
    words = re.findall(r'[a-z]+', line.lower())
    # emit words and increment total counter
    for word in words:
        TOTAL_WORDS += 1
        pkey = getPartitionKey(word)
        print(f'{pkey}\t{word}\t{1}')
        
# emit total count to each partition (note this is a partial total)
############## YOUR CODE HERE ##############
print(f'A\t!total\t{TOTAL_WORDS}')
print(f'B\t!total\t{TOTAL_WORDS}')
print(f'C\t!total\t{TOTAL_WORDS}')
print(f'D\t!total\t{TOTAL_WORDS}')
############## (END) YOUR CODE ##############
