#!/usr/bin/env python

import os
import sys
files = sys.argv[1:]

def norm_dates(fname):
    s, e = fname.split("_")[-1].split(".")[0].split("-")

    while len(s) < 8:
        s += "01"

    if len(e) == 4: e += "12"
    if len(e) == 6: e += "30" 

    return (s, e)

def overlap(r1, r2):
    a, b = r1
    c, d = r2
    return (a <= d and b >= c)


pairs = [(files[i], files[j]) for i in range(len(files)) for j in range(i+1, len(files))] 

for pair in pairs:
#    print(f"Comparing: {pair}")
    r1, r2 = [norm_dates(f) for f in pair]
    if overlap(r1, r2):
        print(f"[ERROR] OVERLAP: {r1} AND {r2}: {pair}")

 

