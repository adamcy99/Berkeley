#!/usr/bin/env python
"""
Mapper script to tokenize words from a line of text.
INPUT:
    a text file
OUTPUT:
    word \t partialCount
    
NOTE: Uncomment line 22 before running.
"""
import re
import sys

# read from standard input
for line in sys.stdin:
    line = line.strip()
    # tokenize
    words = re.findall(r'[a-z]+', line.lower())
    # emit words and count of 1 plus total counter
    for word in words:
        print(f'{word}\t{1}')
        #print(f'total\t{1}')  # part b/c - UNCOMMENT & MAKE YOUR CHANGE HERE
        print(f'!total\t{1}')      # <--- SOLUTION --->