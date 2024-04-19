#!/usr/bin/env python
"""
Mapper script to emit tokenized words from a line of text.
INPUT:
    a text file
OUTPUT:
    word \t partialCount
"""
import re
import sys

# read from standard input
for line in sys.stdin:
    line = line.strip()
    # tokenize
    words = re.findall(r'[a-z]+', line.lower())
    # emit words and count of 1
    for word in words:
        print(f'{word}\t{1}')