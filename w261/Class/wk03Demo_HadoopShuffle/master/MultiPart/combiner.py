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

# read input key-value pairs from standard input
for line in sys.stdin:
    ######### UNCOMMENT & MODIFY AS NEEDED BELOW ############
#    key, value = line.split()       
#    # tally counts from current key
#    if key == cur_word: 
#        cur_count += int(value)
#    # OR emit current total and start a new tally 
#    else: 
#        if cur_word:
#            print(f'{cur_word}\t{cur_count}')
#        cur_word, cur_count  = key, int(value)

## don't forget the last record! 
#print(f'{cur_word}\t{cur_count}')


    part, key, value = line.split()                     # <--- SOLUTION --->  
    # tally counts from current key                     # <--- SOLUTION ---> 
    if key == cur_word:                                 # <--- SOLUTION ---> 
        cur_count += int(value)                         # <--- SOLUTION ---> 
    # OR emit current total and start a new tally       # <--- SOLUTION ---> 
    else:                                               # <--- SOLUTION ---> 
        if cur_word:                                    # <--- SOLUTION ---> 
            print(f'{part}\t{cur_word}\t{cur_count}')   # <--- SOLUTION ---> 
        cur_word, cur_count  = key, int(value)          # <--- SOLUTION ---> 
                                                        # <--- SOLUTION ---> 
# don't forget the last record!                         # <--- SOLUTION ---> 
print(f'{part}\t{cur_word}\t{cur_count}')               # <--- SOLUTION ---> 
