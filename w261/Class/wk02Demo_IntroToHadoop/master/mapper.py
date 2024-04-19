#!/usr/bin/env python
"""
This is a silly mapper to demonstrate some errors.
"""
import sys
import numpy as np  # To use numpy add -cmdenv PATH={PATH} to your Hadoop Job

for line in sys.stdin:
    msg = ("a message"    # missing a parenthesis here
    print(1/0)            # dividing by zero is a no-go