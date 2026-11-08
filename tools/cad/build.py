"""Derive SmartManipulator-X (BCN3D Moveo) kinematics and link meshes from the STEP.

All geometry comes from the faceted STEP of the BCN3D Moveo assembly
(parsed by parse_step.py, links assigned by classify.py). World frame of the
STEP: metres, Y up.
"""
import json
import os
import struct
import sys

import numpy as np

S = np.load("shapes.npz")
I = {k["id"]: k for k in json.load(open("instances.json"))}
L = {int(k): v for k, v in json.load(open("labels.json")).items()}
match = json.load(open("match.json"))
OUT = sys.argv[1] if len(sys.argv) > 1 else "out"
os.makedirs(f"{OUT}/meshes/visual", exist_ok=True)
os.makedirs(f"{OUT}/meshes/collision", exist_ok=True)


def world(i):
    k = I[i]
    T = np.array(k["T"])
    return S[str(k["shape"])] @ T[:3, :3].T + T[:3, 3]


def unit(v):
    return v / np.linalg.norm(v)


def bar_axis(shape):
    i = next(i for i, k in I.items() if k["shape"] == shape)
    p = np.unique(world(i).reshape(-1, 3), axis=0)
    c = p.mean(0)
    v = np.linalg.eigh((p - c).T @ (p - c))[1][:, 2]
    t = (p - c) @ v
    return c + v * (t.max() + t.min()) / 2, v


# ---------------------------------------------------------------- joint axes
Yw = np.array([0.0, 1.0, 0.0])
p2, a2 = bar_axis(861044)      # shoulder axle, 8 x 140 mm
p3, a3 = bar_axis(1650458)     # elbow axle
p5, a5 = bar_axis(2134982)     # wrist pitch axle, 8 x 80 mm
for a in (a3, a5):
    pass
a3 = a3 * np.sign(a3 @ a2)
a5 = a5 * np.sign(a5 @ a2)
j1_xz = np.array([p2[0], p2[2]])  # J1 axis passes through the shoulder axle centre

# base: robot stands on the top of the (dropped) table plate
plate_top = -0.049
dropped = []
keep = {}
for i, lk in L.items():
    w = world(i)
    if w[..., 1].max() < plate_top + 0.001 or (lk == "base" and w[..., 1].min() < plate_top - 0.002):
        # feet under the plate and the screws through it
        dropped.append(i)
        continue
    keep[i] = lk
O = np.array([j1_xz[0], plate_top, j1_xz[1]])

# forward = horizontal, perpendicular to the shoulder axle, towards the arm
f = unit(np.cross(Yw, a2))
if f @ (p5 - O) < 0:
    f = -f


def frame(origin, y, z):
    z = unit(z)
    y = unit(y - z * (y @ z))
    x = np.cross(y, z)
    T = np.eye(4)
    T[:3, 0], T[:3, 1], T[:3, 2], T[:3, 3] = x, y, z, origin
    return T


# y axes chosen so that +angle of J2/J3/J5 bends the arm forward (+x).
F = {}
F["base_link"] = frame(O, np.cross(Yw, f), Yw)
F["link1"] = F["base_link"].copy()                                 # J1 = 0 here
F["link2"] = frame(p2, F["base_link"][:3, 1], p3 - p2)
u = unit(p5 - p3)
F["link3"] = frame(p3, F["link2"][:3, 1], u)
link4_pts = np.concatenate([world(i).reshape(-1, 3) for i, l in keep.items() if l == "link4"])
d34 = max(0.0, ((link4_pts - p3) @ u).min())
y4 = -a5 if (-a5) @ F["link3"][:3, 1] > 0 else a5
F["link4"] = frame(p3 + d34 * u, y4, u)

# gripper geometry (holes found by holes.py)
G_r = np.array([154.60, 388.74, -141.10]) / 1000   # servo horn centre
A_r = np.array([192.20, 383.75, -128.40]) / 1000   # servo gear arm -> right finger
G_l = np.array([128.22, 392.50, -149.69]) / 1000   # idler gear centre
A_l = np.array([90.52, 397.84, -161.96]) / 1000    # idler gear arm -> left finger
P_r = np.array([151.93, 379.26, -159.86]) / 1000   # right pivot arm on the plate
P_l = np.array([138.73, 381.12, -164.15]) / 1000   # left pivot arm on the plate
n_g = unit(np.cross(A_r - G_r, P_r - G_r))         # gear axis = gripper plane normal
fing = np.concatenate([world(i).reshape(-1, 3) for i, l in keep.items() if l.startswith("finger")])
grip_mid = (G_r + G_l) / 2
z5 = (fing.mean(0) - p5)
F["link5"] = frame(p5, y4, z5 - y4 * (z5 @ y4))

# joint angles of the assembly pose (for information)
def ang(Fa, Fb, axis):
    R = Fa[:3, :3].T @ Fb[:3, :3]
    return {"z": np.arctan2(R[1, 0], R[0, 0]), "y": np.arctan2(R[0, 2], R[2, 2])}[axis]


pose = {
    "j2_shoulder": ang(F["link1"], F["link2"], "y"),
    "j3_elbow": ang(F["link2"], F["link3"], "y"),
    "j4_forearm_roll": ang(F["link3"], F["link4"], "z"),
    "j5_wrist": ang(F["link4"], F["link5"], "y"),
}


def local(T, p):
    return (p - T[:3, 3]) @ T[:3, :3]


lengths = {
    "j2_origin_z": local(F["link1"], p2),
    "j3_origin": local(F["link2"], p3),
    "j4_origin": local(F["link3"], F["link4"][:3, 3]),
    "j5_origin": local(F["link4"], p5),
}

# gripper sub-frames: same orientation as link5, origins on the pivots
R5 = F["link5"]
for name, p in (("servo_gear", G_r), ("idler_gear", G_l), ("pivot_right", P_r), ("pivot_left", P_l)):
    T = R5.copy(); T[:3, 3] = p; F[name] = T
T = R5.copy(); T[:3, 3] = A_r; F["finger_right"] = T
T = R5.copy(); T[:3, 3] = A_l; F["finger_left"] = T
axis_g = n_g @ R5[:3, :3]   # gear axis in link5 frame

# ------------------------------------------------------------ gripper range
def rot(axis, a):
    axis = unit(axis); K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K


fr = np.concatenate([world(i).reshape(-1, 3) for i, l in keep.items() if l == "finger_right"])
fl = np.concatenate([world(i).reshape(-1, 3) for i, l in keep.items() if l == "finger_left"])
def finger_gap(theta):
    # right finger translates with the servo gear (+theta), left with the idler (-theta)
    dr = rot(n_g, theta) @ (A_r - G_r) - (A_r - G_r)
    dl = rot(n_g, -theta) @ (A_l - G_l) - (A_l - G_l)
    c = np.cross(n_g, unit(grip_mid - p5))       # opening direction (in plane, across)
    right = (fr + dr) @ c; left = (fl + dl) @ c
    if np.median(right) > np.median(left):
        return right.min() - left.max()
    return left.min() - right.max()


ths = np.radians(np.arange(-90, 91, 1))
gaps = np.array([finger_gap(t) for t in ths])

# --------------------------------------------------------------------- meshes
def decimate(tris, cell):
    v = tris.reshape(-1, 3)
    q = np.round(v / cell).astype(np.int64)
    uq, inv = np.unique(q, axis=0, return_inverse=True)
    inv = inv.reshape(-1)
    acc = np.zeros((len(uq), 3)); cnt = np.zeros(len(uq))
    np.add.at(acc, inv, v); np.add.at(cnt, inv, 1)
    verts = acc / cnt[:, None]
    f = inv.reshape(-1, 3)
    f = f[(f[:, 0] != f[:, 1]) & (f[:, 1] != f[:, 2]) & (f[:, 0] != f[:, 2])]
    f = np.unique(np.sort(f, axis=1), axis=0, return_index=True)[1], f
    f = f[1][np.sort(f[0])]
    return verts[f]


def write_stl(path, tris):
    tris = tris.astype(np.float32)
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-20
    rec = np.zeros(len(tris), dtype=[("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")])
    rec["n"] = n; rec["v"] = tris.reshape(-1, 9)
    with open(path, "wb") as fh:
        fh.write(b"SmartManipulator-X mesh from BCN3D Moveo CAD".ljust(80, b" "))
        fh.write(struct.pack("<I", len(tris))); fh.write(rec.tobytes())


printed = {int(s) for s, (name, err) in match.items() if err <= 0.1 or "Tapa" in name}
groups = {}
for i, lk in keep.items():
    kind = "printed" if I[i]["shape"] in printed else "hardware"
    groups.setdefault((lk, kind), []).append(world(i))

stats = {}
for (lk, kind), parts in sorted(groups.items()):
    T = F["base_link"] if lk in ("base", "ebox") else F[lk]
    tris = np.concatenate(parts)
    loc = (tris - T[:3, 3]) @ T[:3, :3]
    cell = {"printed": 0.0012, "hardware": 0.0022}[kind]
    if lk in ("base", "ebox"):
        cell *= 1.6
    if lk.startswith(("finger", "pivot", "servo", "idler")):
        cell = 0.0008
    vis = decimate(loc, cell)
    write_stl(f"{OUT}/meshes/visual/{lk}_{kind}.stl", vis)
    stats[f"{lk}_{kind}"] = (len(tris), len(vis))
for lk in sorted({l for l, _ in groups}):
    T = F["base_link"] if lk in ("base", "ebox") else F[lk]
    tris = np.concatenate([np.concatenate(v) for (l, k), v in groups.items() if l == lk])
    loc = (tris - T[:3, 3]) @ T[:3, :3]
    from scipy.spatial import ConvexHull
    v = np.unique(loc.reshape(-1, 3), axis=0)
    h = ConvexHull(v)
    col = v[h.simplices]
    # outward winding
    cen = v[h.vertices].mean(0)
    nn = np.cross(col[:, 1] - col[:, 0], col[:, 2] - col[:, 0])
    flip = ((col[:, 0] - cen) * nn).sum(1) < 0
    col[flip] = col[flip][:, [0, 2, 1]]
    write_stl(f"{OUT}/meshes/collision/{lk}.stl", col)
    stats[f"{lk}_collision"] = (len(tris), len(col))

# tool point: between the fingertips, on the gripper centre line
tip = local(F["link5"], fing).max(0)[2]

res = {
    "origin_O_mm": (O * 1000).round(2).tolist(),
    "pose_assembly_deg": {k: round(float(np.degrees(v)), 2) for k, v in pose.items()},
    "lengths_mm": {k: (np.array(v) * 1000).round(2).tolist() for k, v in lengths.items()},
    "axis_check": {"a2.Y": float(a2 @ Yw), "a3.a2": float(a3 @ a2), "u.a3": float(u @ a3), "u.a5": float(u @ a5)},
    "gear_axis_link5": axis_g.round(4).tolist(),
    "gripper_points_link5_mm": {n: (local(F["link5"], p) * 1000).round(2).tolist() for n, p in
                                (("servo_gear", G_r), ("idler_gear", G_l), ("pivot_right", P_r), ("pivot_left", P_l))},
    "finger_offsets_mm": {"right": ((A_r - G_r) @ R5[:3, :3] * 1000).round(2).tolist(),
                          "left": ((A_l - G_l) @ R5[:3, :3] * 1000).round(2).tolist()},
    "tool_z_mm": round(float(tip * 1000), 2),
    "gap_assembly_mm": round(float(finger_gap(0.0) * 1000), 2),
    "gap_vs_theta": [(int(round(np.degrees(t))), round(float(g * 1000), 1)) for t, g in zip(ths, gaps) if int(round(np.degrees(t))) % 10 == 0],
    "mesh_tris": stats,
    "dropped": len(dropped),
}
json.dump(res, open(f"{OUT}/geometry.json", "w"), indent=1)
np.savez(f"{OUT}/frames.npz", **F)
print(json.dumps(res, indent=1))
