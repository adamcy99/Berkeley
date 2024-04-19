#!/usr/bin/env python
"""
Mapper script to count upper and lowercase words.      # <--- SOLUTION --->
INPUT:                                                 # <--- SOLUTION --->
    a text file                                        # <--- SOLUTION --->
OUTPUT:                                                # <--- SOLUTION --->
    upper \t 1  or lower \t 1                          # <--- SOLUTION --->    
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
        elif word[0].islower():                 # <--- SOLUTION --->
            print(f"lower\t{1}")                # <--- SOLUTION --->
        ############ (END) YOUR CODE #########