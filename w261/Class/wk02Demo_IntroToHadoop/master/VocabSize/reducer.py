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
    word, count = line.split()            # <--- SOLUTION --->
    if word != cur_word:                  # <--- SOLUTION --->
        word_count += count               # <--- SOLUTION --->
        cur_word = word                   # <--- SOLUTION --->
print(f"NumUniqueWords\t{word_count}")    # <--- SOLUTION --->
############ (END) YOUR CODE #########
