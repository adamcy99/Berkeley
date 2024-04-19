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
    ########## UNCOMMENT & MODIFY AS NEEDED BELOW #########
#    key, value = line.split()
#    # tally counts from current key
#    if key == cur_word: 
#        cur_count += int(value)
#    # OR ...  
#    else:
#        # store word count total
#        if cur_word == '!total': 
#            total = float(cur_count)
#        # emit realtive frequency
#        if cur_word:
#            print(f'{cur_word}\t{cur_count/total}')
#        # and start a new tally 
#        cur_word, cur_count  = key, int(value)
#
## don't forget the last record! 
#print(f'{cur_word}\t{cur_count/total}')

    part, key, value = line.split()                 # <--- SOLUTION --->
    sys.stderr.write(f'reporter:counter:MyCounters,{part},1\n')  # <--- SOLUTION --->
    # tally counts from current key                 # <--- SOLUTION --->
    if key == cur_word:                             # <--- SOLUTION --->
        cur_count += int(value)                     # <--- SOLUTION --->
    # OR ...                                        # <--- SOLUTION --->
    else:                                           # <--- SOLUTION --->
        # store word count total                    # <--- SOLUTION --->
        if cur_word == '!total':                    # <--- SOLUTION --->
            total = float(cur_count)                # <--- SOLUTION --->
        # emit realtive frequency                   # <--- SOLUTION --->
        if cur_word and cur_word != '!total':       # <--- SOLUTION --->
            print(f'{cur_word}\t{cur_count/total}') # <--- SOLUTION --->
        # and start a new tally                     # <--- SOLUTION --->
        cur_word, cur_count  = key, int(value)      # <--- SOLUTION --->
                                                    # <--- SOLUTION --->
## don't forget the last record!                    # <--- SOLUTION --->
print(f'{cur_word}\t{cur_count/total}')             # <--- SOLUTION --->