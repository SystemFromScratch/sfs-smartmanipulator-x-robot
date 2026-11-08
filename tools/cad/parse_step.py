"""Parse a faceted STEP (POLY_LOOP triangles + MAPPED_ITEM instances) into numpy.

Output: shapes.npz with, per shape map id, triangles in shape frame, and
instances.json with each mapped item's shape id and 4x4 transform.
"""
import json
import re
import sys

import numpy as np

path, out_dir = sys.argv[1], sys.argv[2]
want = {"CARTESIAN_POINT", "DIRECTION", "AXIS2_PLACEMENT_3D", "POLY_LOOP", "FACE_OUTER_BOUND",
        "FACE_SURFACE", "CLOSED_SHELL", "FACETED_BREP", "ADVANCED_BREP_SHAPE_REPRESENTATION",
        "REPRESENTATION_MAP", "MAPPED_ITEM"}
ent = {}
rx = re.compile(r"^#(\d+)=([A-Z_0-9]+)\((.*)\);\s*$")
buf = ""
with open(path, "r", errors="ignore") as f:
    for line in f:
        buf += line.strip()
        if not buf.endswith(";"):
            continue
        m = rx.match(buf)
        buf = ""
        if m and m.group(2) in want:
            ent[int(m.group(1))] = (m.group(2), m.group(3))
print("entities", len(ent), file=sys.stderr)

refs = lambda s: [int(x) for x in re.findall(r"#(\d+)", s)]
nums = lambda s: [float(x) for x in re.findall(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", s.split("(", 1)[1])]

pts = {}
def point(i):
    if i not in pts:
        pts[i] = nums(ent[i][1])[:3]
    return pts[i]

def placement(i):
    o, z, x = refs(ent[i][1])[:3]
    o = np.array(point(o)); z = np.array(nums(ent[z][1])[:3]); x = np.array(nums(ent[x][1])[:3])
    z /= np.linalg.norm(z); x = x - z * (x @ z); x /= np.linalg.norm(x); y = np.cross(z, x)
    T = np.eye(4); T[:3, 0], T[:3, 1], T[:3, 2], T[:3, 3] = x, y, z, o
    return T

shapes = {}
for i, (t, a) in ent.items():
    if t != "REPRESENTATION_MAP":
        continue
    origin, rep = refs(a)[:2]
    brep = [r for r in refs(ent[rep][1]) if ent.get(r, ("",))[0] == "FACETED_BREP"][0]
    shell = refs(ent[brep][1])[0]
    tris = []
    for face in refs(ent[shell][1]):
        bound = refs(ent[face][1])[0]
        loop = refs(ent[bound][1])[0]
        p = [point(k) for k in refs(ent[loop][1])]
        for k in range(1, len(p) - 1):  # fan, in case of polygons
            tris.append((p[0], p[k], p[k + 1]))
    T0 = placement(origin)
    shapes[i] = (np.array(tris, dtype=np.float64), T0)

inst = []
for i, (t, a) in ent.items():
    if t != "MAPPED_ITEM":
        continue
    m, target = refs(a)[:2]
    T = placement(target) @ np.linalg.inv(shapes[m][1])
    inst.append({"id": i, "shape": m, "T": T.tolist()})

np.savez_compressed(f"{out_dir}/shapes.npz", **{str(k): v[0] for k, v in shapes.items()})
json.dump(inst, open(f"{out_dir}/instances.json", "w"))
print("shapes", len(shapes), "instances", len(inst), file=sys.stderr)
