"""Forward kinematics of a plain URDF with mesh visuals, rendered with render.py.

fk_render.py robot.urdf mesh_root out.png 'j2_shoulder=0.5,gripper=1.2' [collision]
"""
import sys
import xml.etree.ElementTree as ET

import numpy as np

sys.path.insert(0, ".")
from render import render
from stl import load_stl

urdf, root, out = sys.argv[1], sys.argv[2], sys.argv[3]
q = dict((k, float(v)) for k, v in (a.split("=") for a in sys.argv[4].split(",") if a)) if len(sys.argv) > 4 else {}
use_col = len(sys.argv) > 5 and sys.argv[5] == "collision"
r = ET.parse(urdf).getroot()
joints = {}
for j in r.findall("joint"):
    o = j.find("origin")
    ax = j.find("axis")
    m = j.find("mimic")
    joints[j.find("child").get("link")] = dict(
        name=j.get("name"), type=j.get("type"), parent=j.find("parent").get("link"),
        xyz=np.array([float(x) for x in o.get("xyz").split()]),
        axis=np.array([float(x) for x in ax.get("xyz").split()]) if ax is not None else None,
        mimic=(m.get("joint"), float(m.get("multiplier"))) if m is not None else None)


def rot(axis, a):
    axis = axis / np.linalg.norm(axis)
    K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K


cache = {"world": np.eye(4)}


def T(link):
    if link in cache:
        return cache[link]
    j = joints[link]
    A = np.eye(4)
    A[:3, 3] = j["xyz"]
    if j["type"] != "fixed":
        v = q.get(j["mimic"][0], 0.0) * j["mimic"][1] if j["mimic"] else q.get(j["name"], 0.0)
        A[:3, :3] = rot(j["axis"], v)
    cache[link] = T(j["parent"]) @ A
    return cache[link]


groups = []
tag = "collision" if use_col else "visual"
import os
only = set(os.environ.get("ONLY", "").split(",")) - {""}
for l in r.findall("link"):
    if only and l.get("name") not in only:
        continue
    for v in l.findall(tag):
        mesh = v.find("geometry/mesh")
        if mesh is None:
            continue
        path = mesh.get("filename").split("meshes/", 1)[1]
        t = load_stl(f"{root}/{path}")
        W = T(l.get("name"))
        w = t @ W[:3, :3].T + W[:3, 3]
        mat = v.find("material")
        rgb = (0.95, 0.55, 0.12) if mat is not None and "printed" in mat.get("name") else (0.35, 0.35, 0.4)
        if use_col:
            rgb = tuple(np.random.default_rng(abs(hash(l.get("name"))) % 2**32).uniform(0.2, 1, 3))
        groups.append((l.get("name"), w, rgb))
marks = [(n, T(n)[:3, 3], "red") for n in ("link2", "link3", "link4", "link5", "tool_link")]
render(groups, out, views=(("front (x right, z up)", 0, 2, 1), ("side (y right, z up)", 1, 2, 0), ("top", 0, 1, 2)),
       size=6, maxtri=400000, marks=marks)
