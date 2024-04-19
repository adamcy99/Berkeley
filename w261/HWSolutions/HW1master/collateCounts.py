#!/usr/bin/env python
"""
This script reads word counts from STDIN and combines
the counts for any duplicated words.

INPUT & OUTPUT FORMAT:
    word \t count
USAGE:
    python collateCounts.py < yourCountsFile.txt

Instructions:
    For Q6 - Use the provided code as is. (you'll need to uncomment it)
    For Q7 - Delete or comment out the section marked "PROVIDED CODE" &
             replace it with your own implementation. Your solution 
             should not use a dictionary or store counts in any way - 
             just print them as soon as you've added them. HINT: you've
             modified the framework script to ensure that the input
             is alphabetized; how can you use that to your advantage?
"""

# imports
import sys
from collections import defaultdict

########### PROVIDED IMPLEMENTATION ##############  
##### uncomment to run
# counts = defaultdict(int)
# # stream over lines from Standard Input
# for line in sys.stdin:
#     # extract words & counts
#     word, count  = line.split()
#     # tally counts
#     counts[word] += int(count)
# # print counts
# for wrd, count in counts.items():
#     print("{}\t{}".format(wrd,count))
########## (END) PROVIDED IMPLEMENTATION #########

################# YOUR CODE HERE #################
current_word = None                                     # <---SOLUTION--->
current_count = 0                                       # <---SOLUTION--->
for line in sys.stdin:                                  # <---SOLUTION--->
    word, count = line.split()                          # <---SOLUTION--->
    if current_word is None or word == current_word:    # <---SOLUTION--->
        current_count += int(count)                     # <---SOLUTION--->
    elif current_word is not None:                      # <---SOLUTION--->
        print(f"{current_word}\t{current_count}")       # <---SOLUTION--->
        current_count = int(count)                      # <---SOLUTION--->
    current_word = word                                 # <---SOLUTION--->
# don't forget the last word!                           # <---SOLUTION--->
print(f"{current_word}\t{current_count}")               # <---SOLUTION--->
################ (END) YOUR CODE #################
