#!/usr/bin/env python
"""
Reducer script to count unique words.
INPUT:
    word \t 1  (sorted alphabetically)
OUTPUT:
    an integer count
"""
import re
import sys

cur_word = None
word_count = 0
# read from standard input
for line in sys.stdin:
    line = line.strip()

############ YOUR CODE HERE #########
    if line == cur_word:
        pass
    else:
        if cur_word:
            word_count += 1
        cur_word = line
word_count += 1
print(f'{word_count}')




############ (END) YOUR CODE #########
