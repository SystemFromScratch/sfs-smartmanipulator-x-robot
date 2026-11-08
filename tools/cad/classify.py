"""Assign every STEP instance to a robot link by proximity to anchor parts."""
import json
import sys

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, ".")
S = np.load("shapes.npz")
I = json.load(open("instances.json"))


def world(k):
    T = np.array(k["T"])
    return S[str(k["shape"])] @ T[:3, :3].T + T[:3, 3]


ANCHORS = {
    "base": [42880, 3757880, 3476936],
    "ebox": [3642470, 3505246, 3676622],
    "link1": [982100, 661366, 784316, 846788],
    "link2": [1060258, 1101820, 1521638, 1543702],
    "link3": [1690710, 1740320],
    "link4": [1961682, 2007130],
    "link5": [2097740, 2122776, 2198796, 2235854],
    "servo_gear": [2508226],
    "idler_gear": [2418026],
    "finger_right": [2339966],
    "finger_left": [2289100],
}
DROP = {3475042, 3445202}  # 0.7 m table plate; loose servo cable
INSTANCE_ANCHORS = {3832895: "pivot_right", 3832903: "pivot_left"}

inst = {k["id"]: k for k in I}
W = {k["id"]: world(k) for k in I if k["shape"] not in DROP}
label = {}
for lk, shapes in ANCHORS.items():
    for i, k in inst.items():
        if k["shape"] in shapes and i in W:
            label[i] = lk
for i, lk in INSTANCE_ANCHORS.items():
    label[i] = lk

trees = {}
for i, lk in label.items():
    trees[i] = cKDTree(np.unique(W[i].reshape(-1, 3), axis=0))

report = []
for i, w in W.items():
    if i in label:
        continue
    p = np.unique(w.reshape(-1, 3), axis=0)
    if len(p) > 3000:
        p = p[np.random.default_rng(0).choice(len(p), 3000, replace=False)]
    best = None
    for j, t in trees.items():
        d = t.query(p, k=1)[0].min()
        if best is None or d < best[0]:
            best = (d, j)
    label[i] = label[best[1]]
    report.append((i, inst[i]["shape"], label[i], round(best[0] * 1000, 2), best[1]))

json.dump({str(k): v for k, v in label.items()}, open("labels.json", "w"))
for r in sorted(report, key=lambda r: (r[2], r[1])):
    print(*r)
