#!/usr/bin/env python
"""
Combiner script to add counts with the same key.
INPUT:
    word \t partialCount
OUTPUT:
    word \t totalCount
"""
import sys

# initialize trackers
cur_word = None
cur_count = 0
cur_pkey = None

# read input key-value pairs from standard input
for line in sys.stdin:
    ######### UNCOMMENT & MODIFY AS NEEDED BELOW ############
   pkey, key, value = line.split()       
   # tally counts from current key
   if key == cur_word: 
       cur_count += int(value)
   # OR emit current total and start a new tally 
   else: 
       if cur_word:
           print(f'{cur_pkey}\t{cur_word}\t{cur_count}')
       cur_pkey, cur_word, cur_count  = pkey, key, int(value)

## don't forget the last record! 
print(f'{cur_pkey}\t{cur_word}\t{cur_count}')













