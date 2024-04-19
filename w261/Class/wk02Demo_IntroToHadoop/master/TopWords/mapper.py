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
    word, count = line.split()            # <--- SOLUTION --->
    print(f"{count}\t{word}")             # <--- SOLUTION --->
############ (END) YOUR CODE #########