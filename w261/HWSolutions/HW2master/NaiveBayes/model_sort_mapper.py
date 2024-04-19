#!/usr/bin/env python
"""
Mapper to help partition our model file based
on the conditional probability in Spam & Ham
INPUT:
    word \t hamCount,spamCount,pHam,pSpam
OUTPUT:
    word \t hamCount,spamCount,pHam,pSpam \t maxClass \t maxClassProbabilty
"""
import sys
for line in sys.stdin:
    word, payload = line.split()
    ham_cProb, spam_cProb = payload.strip().split(',')[2:]
    if float(ham_cProb) >= float(spam_cProb):
        maxClass, maxClassP = 'ham', ham_cProb
    else:
        maxClass, maxClassP = 'spam', spam_cProb
    print(f"{word}\t{payload}\t{maxClass}\t{maxClassP}")