"""Name the STEP shapes by matching them to the BCN3D printed-part STL files.

match_parts.py <BCN3D-Moveo checkout>  ->  match.json {shape: [stl name, error]}
Surface area and principal extents are compared; error <= 0.1 is a match.
"""
import glob
import json
import sys

import numpy as np

from stl import area, load_stl, pdims

ref = {}
for f in glob.glob(f"{sys.argv[1]}/STL files/*/*.[sS][tT][lL]"):
    t = load_stl(f) / 1000.0
    ref[f.split("STL files/")[1]] = (area(t), pdims(t))
S = np.load("shapes.npz")
res = {}
for s in S.files:
    t = S[s]
    a, d = area(t), pdims(t)
    if a < 0.002:
        continue
    name, (ra, rd) = min(ref.items(), key=lambda kv: abs(kv[1][0] - a) / a + np.abs(kv[1][1] - d).sum() / d.sum())
    res[s] = (name, float(abs(ra - a) / a + np.abs(rd - d).sum() / d.sum()))
json.dump(res, open("match.json", "w"), indent=1)
