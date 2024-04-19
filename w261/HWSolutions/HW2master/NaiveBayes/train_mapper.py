#!/usr/bin/env python
"""
Mapper reads in text documents and emits word counts by class.
INPUT:                                                    # <--- SOLUTION --->
    DocID \t true_class \t subject \t body                # <--- SOLUTION --->
OUTPUT:                                                   # <--- SOLUTION --->
    word \t class0_partialCount,class1_partialCount       # <--- SOLUTION --->
    
INPUT:
    <specify record format here>
OUTPUT:
    <specify record format here>
    
Instructions:
    You know what this script should do, go for it!
    (As a favor to the graders, please comment your code clearly!)
    
    A few reminders:
    1) To make sure your results match ours please be sure
       to use the same tokenizing that we have provided in
       all the other jobs:
         words = re.findall(r'[a-z]+', text-to-tokenize.lower())
         
    2) Don't forget to handle the various "totals" that you need
       for your conditional probabilities and class priors.
"""
##################### YOUR CODE HERE ####################
import re                                                   # <--- SOLUTION --->
import sys                                                  # <--- SOLUTION --->
import numpy as np                                          # <--- SOLUTION --->

# initialize class counters                                 # <--- SOLUTION --->
docTotals = np.array([0,0])                                 # <--- SOLUTION --->
wordTotals = np.array([0,0])                                # <--- SOLUTION --->
                                                            # <--- SOLUTION --->
# read from standard input                                  # <--- SOLUTION --->
for line in sys.stdin:                                      # <--- SOLUTION --->
    # parse input and tokenize                              # <--- SOLUTION --->
    docID, class_, subj, body = line.lower().split('\t')    # <--- SOLUTION --->
    words = re.findall(r'[a-z]+', subj + ' ' + body)        # <--- SOLUTION --->
    increment = [1,0] if class_ =='0' else [0,1]            # <--- SOLUTION --->
                                                            # <--- SOLUTION --->    
    # update class counts                                   # <--- SOLUTION --->
    docTotals += increment                                  # <--- SOLUTION --->
    wordTotals += np.array(increment) * len(words)          # <--- SOLUTION --->
                                                            # <--- SOLUTION --->    
    # emit words with a count for each class (0,1 or 1,0)   # <--- SOLUTION --->
    for word in words:                                      # <--- SOLUTION --->
        print("{}\t{},{}".format(word, *increment))         # <--- SOLUTION --->
                                                            # <--- SOLUTION --->
# finaly, emit totals with special key (order inversion)    # <--- SOLUTION --->
print("*docTotals\t{},{}".format(*docTotals))               # <--- SOLUTION --->
print("*wordTotals\t{},{}".format(*wordTotals))             # <--- SOLUTION --->
##################### (END) YOUR CODE #####################