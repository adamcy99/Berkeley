#!/usr/bin/env python
"""
Reducer aggregates word counts by class and emits frequencies
with plus one Laplace Smoothing.
    
Instructions:
    Start by copying your unsmoothed reducer code
    (including the rest of the docstring info^^).
    Then make the necessary modifications so that you
    perform Laplace plus-k smoothing. See equation 13.7 
    in Manning, Raghavan and Shutze for details.
    
    Although we'll only look at results for K=1 (plus 1)
    smoothing its a good idea to set K as a variable
    at the top of your script so that its easy to change
    if you want to explore the effect of different 'K's.
    
    Please clearly mark the modifications you make to
    implement smoothing with a comment like:
            # LAPLACE MODIFICATION HERE 
"""
##################### YOUR CODE HERE ####################
import sys                                                  # <--- SOLUTION --->
import numpy as np                                          # <--- SOLUTION --->
                                                            # <--- SOLUTION ---> 
# helper function to emit records correctly formatted       # <--- SOLUTION --->
def EMIT(*args):                                            # <--- SOLUTION --->
    print('{}\t{},{},{},{}'.format(*args))                  # <--- SOLUTION --->
                                                            # <--- SOLUTION --->
# Laplace Smoothing Parameters                              # <--- SOLUTION --->
#V = 5065.0  # Enron vocab size                             # <--- SOLUTION --->
V = 4555.0 # Enron training set vocab size                  # <--- SOLUTION --->
#V = 6.0  # China vocab size                                # <--- SOLUTION --->
k = 1                                                       # <--- SOLUTION --->
                                                            # <--- SOLUTION --->    
# initialize trackers [ham, spam]                           # <--- SOLUTION --->
docTotals = np.array([0.0,0.0])                             # <--- SOLUTION --->
wordTotals = np.array([0.0, 0.0])                           # <--- SOLUTION --->
cur_word, cur_counts = None, np.array([0,0])                # <--- SOLUTION --->
                                                            # <--- SOLUTION --->
# read from standard input                                  # <--- SOLUTION --->
for line in sys.stdin:                                      # <--- SOLUTION --->
    wrd, counts = line.split()                              # <--- SOLUTION --->
    counts = [int(c) for c in counts.split(',')]            # <--- SOLUTION --->
                                                            # <--- SOLUTION --->    
    # store totals, add or emit counts and reset            # <--- SOLUTION ---> 
    if wrd == "*docTotals":                                 # <--- SOLUTION ---> 
        docTotals += counts                                 # <--- SOLUTION --->
    elif wrd == "*wordTotals":                              # <--- SOLUTION ---> 
        wordTotals += counts                                # <--- SOLUTION --->        
    elif wrd == cur_word:                                   # <--- SOLUTION --->
        cur_counts += counts                                # <--- SOLUTION --->
    else:                                                   # <--- SOLUTION --->
        if cur_word:                                        # <--- SOLUTION --->
            # LAPLACE MODIFICATION HERE                     # <--- SOLUTION ---> 
            freq = (cur_counts + [k,k])/(wordTotals + [V,V])# <--- SOLUTION --->
            EMIT(cur_word, *tuple(cur_counts)+tuple(freq))  # <--- SOLUTION --->
        cur_word, cur_counts  = wrd, np.array(counts)       # <--- SOLUTION --->
                                                            # <--- SOLUTION --->
# last record  (LAPLACE MODIFICATION HERE)                  # <--- SOLUTION ---> 
freq = (cur_counts + [k,k])/(wordTotals + [V,V])            # <--- SOLUTION --->
EMIT(cur_word, *tuple(cur_counts)+tuple(freq))              # <--- SOLUTION --->
                                                            # <--- SOLUTION --->
# class priors                                              # <--- SOLUTION --->
priors = tuple(docTotals) + tuple(docTotals/sum(docTotals)) # <--- SOLUTION --->
EMIT('ClassPriors', *priors)                                # <--- SOLUTION --->
##################### (END) CODE HERE ####################