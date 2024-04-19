#!/usr/bin/env python
"""





<write your description here>
INPUT:
    <specify record format here>
OUTPUT:
    <specify record format here> 
"""
import re
import sys

# read from standard input
for line in sys.stdin:
    line = line.strip()
    
    for word in line.split():
        # emit 'upper' or 'lower' as appropriate
        if word[0].isupper():
            print(f"upper\t{1}")
        ############ YOUR CODE HERE #########
        else:
            print(f"lower\t{1}")

        ############ (END) YOUR CODE #########