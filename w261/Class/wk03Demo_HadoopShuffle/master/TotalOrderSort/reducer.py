#!/usr/bin/env python
"""
Reducer to remove partition keys and print results.

INPUT:
    partitionKey \t word \t relative-frequency
OUTPUT:
    word \t relative frequency
"""
import sys

for line in sys.stdin: 
    key, word, freq = line.strip().split()   
    print(f"{word}\t{freq}")    


    
    
    
    