#!/usr/bin/env python
"""
Reducer script to add counts with the same key and
divide by total count to get relative frequency.
INPUT:
    word \t partialCount
OUTPUT:
    word \t totalCount
"""
import sys

# initialize trackers
cur_word = None
cur_count = 0
total = 0

# read input key-value pairs from standard input
for line in sys.stdin:
    key, value = line.split()
    # tally counts from current key
    if key == cur_word: 
        cur_count += int(value)
    # OR ...  
    else:
        # store word count total
        #if cur_word == 'total':   # part b/c - UNCOMMENT & MAKE YOUR CHANGE HERE    
        if cur_word == '!total':         # <--- SOLUTION --->
            total = float(cur_count)  
        # emit realtive frequency
        if cur_word:
            print(f'{cur_word}\t{cur_count/total}')
        # and start a new tally 
        cur_word, cur_count  = key, int(value)

# don't forget the last record! 
print(f'{cur_word}\t{cur_count/total}')