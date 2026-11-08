#******************************************************************************
# SmartManipulator-X: Robot PC
#
# Description: Draws the real SmartManipulator-X arm (the robot description
#              generated from the BCN3D Moveo CAD: URDF/Xacro kinematics and the
#              visual STL meshes) in the isometric projection of svgkit, as
#              animation frames for the hero illustration (tools/docs/diagrams.py).
#
# Author:      Anton Vynohradov
# Email:       avynohradov@systemfromscratch.com
# License:     Apache License 2.0
# Copyright (c) 2026 Anton Vynohradov
#
# SPDX-License-Identifier: Apache-2.0
#*****************************************************************************

"""Isometric frames of the real arm, from the robot description.

1. The kinematic tree is read from smartmanipulator_x.urdf.xacro (plain <link> and
   <joint> elements; xacro-only parts such as the optional electronics box are skipped).
2. Every visual mesh is simplified once by vertex clustering.
3. For each frame, forward kinematics places the meshes, the triangles are flat shaded
   in the SystemFromScratch® palette, projected like svgkit.Iso and sorted back to front.
4. Visibility comes from an ID buffer drawn with Pillow: only triangles that cover at
   least one pixel of a frame are written, which keeps the SVG small.

Needs numpy and Pillow (python -m pip install numpy pillow)."""

from __future__ import annotations

import math
import os
import struct
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Tuple

import numpy as np

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DESCRIPTION = os.path.join(ROOT, "ros2_ws", "src", "smartmanipulator_x",
                           "smartmanipulator_x_description")
URDF = os.path.join(DESCRIPTION, "urdf", "smartmanipulator_x.urdf.xacro")

COS30 = math.cos(math.radians(30))
VIEW = np.array([1.0, 1.0, 1.0]) / math.sqrt(3.0)       # towards the viewer (svgkit.Iso)
LIGHT = np.array([0.25, 0.55, 1.0]) / np.linalg.norm([0.25, 0.55, 1.0])

# shade ramps, dark to light: printed plastic and metal hardware (motors, screws)
RAMPS = {
    "p": ("#2c3e5c", "#e2eaf6"),
    "h": ("#0c1524", "#5878a3"),
}
LEVELS = 12
MIN_PIXELS = 1


def _hex(rgb: Sequence[float]) -> str:
    return "#" + "".join(f"{int(round(c)):02x}" for c in rgb)


def _ramp(name: str) -> List[str]:
    a, b = (np.array([int(c[i:i + 2], 16) for i in (1, 3, 5)], float) for c in RAMPS[name])
    return [_hex(a + (b - a) * k / (LEVELS - 1)) for k in range(LEVELS)]


def load_stl(path: str) -> np.ndarray:
    data = open(path, "rb").read()
    count = struct.unpack("<I", data[80:84])[0]
    rec = np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")])
    return np.frombuffer(data[84:], dtype=rec, count=count)["v"].reshape(-1, 3, 3).astype(float)


def simplify(tris: np.ndarray, cell: float) -> np.ndarray:
    """Vertex clustering: merge the vertices of each grid cell, drop collapsed triangles."""
    pts = tris.reshape(-1, 3)
    keys = np.floor(pts / cell).astype(np.int64)
    _, inverse = np.unique(keys, axis=0, return_inverse=True)
    inverse = inverse.reshape(-1)
    sums = np.zeros((inverse.max() + 1, 3))
    np.add.at(sums, inverse, pts)
    centers = sums / np.bincount(inverse)[:, None]
    idx = inverse.reshape(-1, 3)
    ok = (idx[:, 0] != idx[:, 1]) & (idx[:, 1] != idx[:, 2]) & (idx[:, 0] != idx[:, 2])
    idx = np.unique(np.sort(idx[ok], axis=1), axis=0)
    return centers[idx]


def _rot(axis: np.ndarray, angle: float) -> np.ndarray:
    axis = axis / np.linalg.norm(axis)
    k = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + math.sin(angle) * k + (1 - math.cos(angle)) * k @ k


@dataclass
class Joint:
    name: str
    kind: str
    parent: str
    xyz: np.ndarray
    axis: np.ndarray
    mimic: Tuple[str, float] | None


@dataclass
class Robot:
    joints: Dict[str, Joint] = field(default_factory=dict)          # by child link
    meshes: List[Tuple[str, str, np.ndarray]] = field(default_factory=list)  # link, ramp, tris

    @classmethod
    def load(cls, cell: float = 0.005) -> "Robot":
        robot = cls()
        root = ET.parse(URDF).getroot()
        for joint in root.findall("joint"):        # direct children only: no xacro:if parts
            origin, axis, mimic = joint.find("origin"), joint.find("axis"), joint.find("mimic")
            robot.joints[joint.find("child").get("link")] = Joint(
                joint.get("name"), joint.get("type"), joint.find("parent").get("link"),
                np.array([float(v) for v in origin.get("xyz").split()]),
                np.array([float(v) for v in axis.get("xyz").split()]) if axis is not None
                else np.zeros(3),
                (mimic.get("joint"), float(mimic.get("multiplier", "1"))) if mimic is not None
                else None)
        for link in root.findall("link"):
            for visual in link.findall("visual"):
                mesh = visual.find("geometry/mesh")
                if mesh is None:
                    continue
                path = os.path.join(DESCRIPTION, "meshes",
                                    mesh.get("filename").split("meshes/", 1)[1])
                ramp = "p" if "printed" in os.path.basename(path) else "h"
                robot.meshes.append((link.get("name"), ramp, simplify(load_stl(path), cell)))
        return robot

    def transforms(self, q: Dict[str, float]) -> Dict[str, np.ndarray]:
        cache: Dict[str, np.ndarray] = {}

        def world(link: str) -> np.ndarray:
            if link in cache:
                return cache[link]
            joint = self.joints.get(link)
            if joint is None:
                cache[link] = np.eye(4)
                return cache[link]
            local = np.eye(4)
            local[:3, 3] = joint.xyz
            if joint.kind != "fixed":
                value = (q.get(joint.mimic[0], 0.0) * joint.mimic[1] if joint.mimic
                         else q.get(joint.name, 0.0))
                local[:3, :3] = _rot(joint.axis, value)
            cache[link] = world(joint.parent) @ local
            return cache[link]

        return {name: world(name) for name, _, _ in self.meshes}


@dataclass
class Placement:
    """Where the robot stands in the svgkit.Iso scene."""
    x: float
    y: float
    z: float
    yaw: float          # rad, about the vertical axis
    units: float        # scene units per metre
    scale: float        # svgkit.Iso.scale (pixels per scene unit)

    def project(self, pts: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        c, s = math.cos(self.yaw), math.sin(self.yaw)
        x = (c * pts[..., 0] - s * pts[..., 1]) * self.units + self.x
        y = (s * pts[..., 0] + c * pts[..., 1]) * self.units + self.y
        z = pts[..., 2] * self.units + self.z
        screen = np.stack([(x - y) * COS30 * self.scale,
                           (x + y) * 0.5 * self.scale - z * self.scale], axis=-1)
        return screen, x + y + z            # screen points, depth (larger = nearer)

    def rotate(self, vec: np.ndarray) -> np.ndarray:
        c, s = math.cos(self.yaw), math.sin(self.yaw)
        return np.stack([c * vec[..., 0] - s * vec[..., 1], s * vec[..., 0] + c * vec[..., 1],
                         vec[..., 2]], axis=-1)


@dataclass
class Frame:
    screen: np.ndarray      # (n, 3, 2)
    depth: np.ndarray       # (n, 3) per vertex, larger = nearer
    shade: List[str]        # css class per triangle
    static: np.ndarray      # bool per triangle: part of the base (does not move)


def frame(robot: Robot, place: Placement, q: Dict[str, float], ramps) -> Frame:
    world = robot.transforms(q)
    screens, depths, shades, static = [], [], [], []
    for link, ramp, tris in robot.meshes:
        t = world[link]
        pts = tris @ t[:3, :3].T + t[:3, 3]
        normal = np.cross(pts[:, 1] - pts[:, 0], pts[:, 2] - pts[:, 0])
        normal = place.rotate(normal)
        length = np.linalg.norm(normal, axis=1)
        keep = length > 1e-12
        normal = normal[keep] / length[keep, None]
        normal *= np.sign(normal @ VIEW)[:, None] + (normal @ VIEW == 0)[:, None]
        light = np.clip(0.10 + 0.90 * np.clip(normal @ LIGHT, 0, 1) ** 1.3, 0, 1)
        screen, depth = place.project(pts[keep])
        screens.append(screen)
        depths.append(depth)
        level = np.minimum((light * LEVELS).astype(int), LEVELS - 1)
        shades.extend(f"{ramp}{k}" for k in level)
        static.append(np.full(len(screen), link == "base_link"))
    screen = np.concatenate(screens)
    depth = np.concatenate(depths)
    order = np.argsort(depth.mean(axis=1), kind="stable")
    return Frame(screen[order], depth[order], [shades[i] for i in order],
                 np.concatenate(static)[order])


def visible(fr: Frame, origin: Tuple[float, float], size: Tuple[int, int]) -> np.ndarray:
    """Triangles that are nearest at the centre of at least one pixel (z-buffer with the
    depth interpolated across each triangle). Hidden parts, such as screws inside the
    printed parts, are dropped even where the back-to-front order would draw them."""
    width, height = size
    zbuf = np.full((height, width), -np.inf)
    owner = np.full((height, width), -1, dtype=np.int64)
    pts = fr.screen - np.asarray(origin)
    for i, ((ax, ay), (bx, by), (cx, cy)) in enumerate(pts):
        det = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(det) < 1e-9:
            continue
        x0, x1 = int(max(min(ax, bx, cx), 0)), int(min(max(ax, bx, cx), width - 1))
        y0, y1 = int(max(min(ay, by, cy), 0)), int(min(max(ay, by, cy), height - 1))
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        w0 = ((by - cy) * (gx - cx) + (cx - bx) * (gy - cy)) / det
        w1 = ((cy - ay) * (gx - cx) + (ax - cx) * (gy - cy)) / det
        w2 = 1 - w0 - w1
        inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not inside.any():
            continue
        za, zb, zc = fr.depth[i]
        z = w0 * za + w1 * zb + w2 * zc
        window = zbuf[y0:y1 + 1, x0:x1 + 1]
        win = inside & (z > window)
        window[win] = z[win]
        owner[y0:y1 + 1, x0:x1 + 1][win] = i
    # a triangle that owns a single pixel is covered by the strokes of its neighbours
    pixels = np.bincount(owner[owner >= 0], minlength=len(fr.screen))
    return pixels >= MIN_PIXELS


def path(tri: np.ndarray) -> str:
    """One triangle in half-pixel units (the groups are drawn with scale(.5))."""
    (ax, ay), (bx, by), (cx, cy) = np.rint(tri * 2).astype(int)
    return f"M{ax} {ay}l{bx - ax} {by - ay} {cx - bx} {cy - by}z"


def svg_frames(place: Placement, poses: Sequence[Dict[str, float]], period: float,
               cell: float = 0.005) -> Tuple[str, str, Tuple[float, float, float, float]]:
    """SVG groups (static base + one group per pose, played forward and back), the CSS
    and the screen bounds. Pose 0 is visible without animation (PDF, reduced motion)."""
    robot = Robot.load(cell)
    ramps = {name: _ramp(name) for name in RAMPS}
    frames = [frame(robot, place, q, ramps) for q in poses]
    allpts = np.concatenate([f.screen.reshape(-1, 2) for f in frames])
    x0, y0 = allpts.min(axis=0) - 2
    x1, y1 = allpts.max(axis=0) + 2
    size = (int(x1 - x0) + 1, int(y1 - y0) + 1)
    masks = [visible(f, (x0, y0), size) for f in frames]

    # the base never moves: draw the union of its visible triangles once, behind the arm
    base = frames[0]
    base_seen = np.zeros(base.static.sum(), bool)
    for f, m in zip(frames, masks):
        base_seen |= m[f.static]
    base_tris = base.screen[base.static][base_seen]
    base_shade = [s for s, st in zip(base.shade, base.static) if st]
    base_shade = [s for s, keep in zip(base_shade, base_seen) if keep]

    def group(tris, shades) -> str:
        runs, last, d = [], None, []
        for tri, shade in zip(tris, shades):
            if shade != last and d:
                runs.append(f'<path class="{last}" d="{"".join(d)}"/>')
                d = []
            last = shade
            d.append(path(tri))
        if d:
            runs.append(f'<path class="{last}" d="{"".join(d)}"/>')
        return "".join(runs)

    parts = [f'<g class="arm-base" transform="scale(.5)">{group(base_tris, base_shade)}</g>']
    n = len(frames)
    slots = list(range(n)) + list(range(n - 2, 0, -1))   # ping-pong
    css = []
    for k, (f, m) in enumerate(zip(frames, masks)):
        keep = m & ~f.static
        hidden = "" if k == 0 else ' visibility="hidden"'
        parts.append(f'<g class="arm arm{k}" transform="scale(.5)"{hidden}>'
                     f'{group(f.screen[keep], [s for s, kp in zip(f.shade, keep) if kp])}</g>')
        steps = []
        for slot, pose in enumerate(slots):
            if pose == k:
                start, stop = 100 * slot / len(slots), 100 * (slot + 1) / len(slots)
                steps.append(f"{start:.3f}%{{visibility:visible}}{stop:.3f}%{{visibility:hidden}}")
        first = "0%{visibility:hidden}" if not steps[0].startswith("0.000%") else ""
        css.append(f"@keyframes arm{k}{{{first}{''.join(steps)}}}"
                   f".arm{k}{{animation:arm{k} {period}s step-end infinite}}")
    css.append("".join(f".{name}{k}{{fill:{color};stroke:{color};stroke-width:1;"
                       f"stroke-linejoin:round}}"
                       for name in RAMPS for k, color in enumerate(ramps[name])))
    css.append("@media (prefers-reduced-motion:reduce){.arm{animation:none}}")
    return "".join(parts), "".join(css), (float(x0), float(y0), float(x1), float(y1))


def smooth_poses(count: int, start: Dict[str, float], stop: Dict[str, float]) -> List[Dict[str, float]]:
    """Poses from start to stop with an ease-in-out profile."""
    poses = []
    for i in range(count):
        s = 0.5 - 0.5 * math.cos(math.pi * i / (count - 1))
        poses.append({j: start[j] + (stop[j] - start[j]) * s for j in start})
    return poses
