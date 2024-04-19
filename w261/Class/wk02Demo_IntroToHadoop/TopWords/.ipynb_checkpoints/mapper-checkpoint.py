#!/usr/bin/env python
"""
Mapper reverses order of key(word) and value(count)
INPUT:
    word \t count
OUTPUT:
    count \t word   
"""
import re
import sys

# read from standard input
for line in sys.stdin:
    line = line.strip()

############ YOUR CODE HERE #########
    # tokenize
    words = re.findall(r'[a-z]+', line.lower())
    counts = re.findall(r'[0-9]+', line.lower())
    # reverses order of key(word) and value(count)
    for word,count in zip(words,counts):
        print(f'{count}\t{word}')

############ (END) YOUR CODE #########