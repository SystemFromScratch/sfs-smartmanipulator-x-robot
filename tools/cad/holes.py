"""Find small cylindrical holes in a flat part: holes.py <instance ids...>."""
import json
import sys

import numpy as np
from scipy.cluster.hierarchy import fcluster, linkage

S = np.load("shapes.npz")
I = {k["id"]: k for k in json.load(open("instances.json"))}


def world(i):
    k = I[i]
    T = np.array(k["T"])
    return S[str(k["shape"])] @ T[:3, :3].T + T[:3, 3]


def fit_circle(p2):
    A = np.c_[2 * p2, np.ones(len(p2))]
    b = (p2 ** 2).sum(1)
    x = np.linalg.lstsq(A, b, rcond=None)[0]
    c = x[:2]
    r = np.sqrt(x[2] + c @ c)
    res = np.abs(np.linalg.norm(p2 - c, axis=1) - r).max()
    return c, r, res


def holes(i, rmax=0.006):
    w = world(i)
    p = np.unique(w.reshape(-1, 3), axis=0)
    c0 = p.mean(0)
    ev, V = np.linalg.eigh((p - c0).T @ (p - c0))
    n = V[:, 0]                      # plate normal
    e1, e2 = V[:, 2], V[:, 1]
    tn = np.cross(w[:, 1] - w[:, 0], w[:, 2] - w[:, 0])
    tn /= np.linalg.norm(tn, axis=1, keepdims=True) + 1e-15
    side = w[np.abs(tn @ n) < 0.2].reshape(-1, 3)
    q = np.unique(np.c_[(side - c0) @ e1, (side - c0) @ e2], axis=0)
    out = []
    if len(q) < 4:
        return n, c0, e1, e2, out
    lab = fcluster(linkage(q, "single"), 0.0012, "distance")
    for l in np.unique(lab):
        pts = q[lab == l]
        if len(pts) < 6:
            continue
        c, r, res = fit_circle(pts)
        span = np.ptp(pts, 0).max()
        if r < rmax and res < 0.0005 and span > 1.5 * r:
            out.append((c0 + c[0] * e1 + c[1] * e2, r))
    return n, c0, e1, e2, out


if __name__ == "__main__":
    for i in map(int, sys.argv[1:]):
        n, c0, *_ , hs = holes(i)
        print(i, I[i]["shape"], "normal", n.round(3))
        for c, r in hs:
            print("   hole d=%.1f mm at" % (2 * r * 1000), (c * 1000).round(2))
