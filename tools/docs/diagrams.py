#******************************************************************************
# SmartManipulator-X: Robot PC
#
# Description: Generates the animated isometric hero illustration of the
#              documentation (docs/assets/images/hero-3d.svg), used on the
#              landing page, the PDF cover and the README. Run after a change:
#                  python tools/docs/diagrams.py
#
# Author:      Anton Vynohradov
# Email:       avynohradov@systemfromscratch.com
# License:     Apache License 2.0
# Copyright (c) 2026 Anton Vynohradov
#
# SPDX-License-Identifier: Apache-2.0
#*****************************************************************************

"""Hero illustration of SmartManipulator-X, built with svgkit.

The scene shows what the project does differently: the unchanged ROBOTIS ROS 2 stack on
the Robot PC sends DYNAMIXEL Protocol 2.0 packets over USB (blue request, green reply);
the SmartFusion2 answers them as virtual DYNAMIXEL devices and drives the stepper motors
through six TMC5160 drivers (the glowing cable). The arm is the real robot description:
the visual STL meshes of smartmanipulator_x_description placed by forward kinematics
from the URDF (hero_robot.py), animated as frames between two poses.

Moving parts start with opacity 0 or at their first pose, because WeasyPrint (PDF cover)
does not run SVG animation. Needs numpy and Pillow (requirements-docs.txt)."""

from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hero_robot import Placement, smooth_poses, svg_frames  # noqa: E402
from svgkit import HERO_DEFS, HERO_STYLE, Iso  # noqa: E402

OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..",
                                    "docs", "assets", "images"))

ARM_LIGHT = "#c9d6ea"
ARM_MID = "#8aa0bf"
ARM_DARK = "#6f86a6"
MOTOR_TOP = "#1b2a40"
MOTOR_LEFT = "#131f31"
MOTOR_RIGHT = "#0e1726"
EDGE = "#2a4870"
ACCENT = "#2f8cff"
GLOW = "#5ea6ff"

HERO_LABEL = ("SmartManipulator-X: a Robot PC running ROS 2 sends DYNAMIXEL packets over USB "
              "to a SmartFusion2 controller, which answers as virtual DYNAMIXEL servos and "
              "drives the stepper motors of a BCN3D Moveo arm through six TMC5160 drivers")


def robot_pc(iso: Iso) -> None:
    """A small industrial PC with ROS 2 in Docker."""
    iso.box(0.6, 4.2, 1.0, 4.2, -0.4, 1.2, MOTOR_TOP, MOTOR_LEFT, MOTOR_RIGHT, EDGE, 1.2)
    for i in range(5):  # cooling fins on the top
        y = 1.4 + i * 0.6
        iso.path([iso.p(1.0, y, 1.21), iso.p(2.2, y, 1.21)], "#22344f", 1.6)
    iso.text(3.3, 2.1, 1.21, "ROBOT PC", 0.36, "#e6edf7", 800, 0.04)
    iso.text(3.3, 3.2, 1.21, "ROS 2 JAZZY", 0.24, GLOW, 600, 0.06)
    iso.led(3.9, 4.2, 0.8)
    iso.led(3.5, 4.2, 0.8, "led-rx", "#5ea6ff", 2.4)


def controller_board(iso: Iso) -> None:
    """M2S Hello FPGA Kit with the SmartFusion2 and six TMC5160 driver modules."""
    p = iso.p
    iso.box(7.0, 15.4, 0.0, 6.4, -0.4, 0, "url(#boardTop)", "#0a1628", "#071122", "#1e3a66", 1.2)
    traces = []
    for i in range(5):
        y = 2.0 + i * 0.55
        traces.append([p(8.9, y), p(8.1, y), p(7.8, y - 0.3), p(7.3, y - 0.3)])
    for i in range(6):
        y = 0.75 + i * 0.95
        traces.append([p(12.0, 3.2), p(12.4, y), p(13.1, y)])
    for trace in traces:
        iso.path(trace, "#1d5fbf", 1.3, ' opacity="0.7"')
    # USB connector on the left edge
    iso.box(7.0, 7.7, 2.3, 3.2, 0, 0.45, ARM_LIGHT, ARM_MID, ARM_DARK)
    # SmartFusion2 with pins
    for i in range(6):
        c = 2.15 + i * 0.45
        iso.box(c + 7.0 - 0.08 + 1.0, c + 7.0 + 0.08 + 1.0, 4.45, 4.7, 0, 0.12,
                "#8fa6c6", "#6b819f", "#5a6f8b")
        iso.box(11.95, 12.2, c - 0.08, c + 0.08, 0, 0.12, "#8fa6c6", "#6b819f", "#5a6f8b")
    iso.box(9.0, 12.0, 1.7, 4.5, 0, 0.7, "url(#chipTop)", "#0a1322", "#060d18", ACCENT, 1.0)
    iso.text(10.5, 2.95, 0.71, "SmartFusion2", 0.36, "#e6edf7", 800, 0.02)
    iso.text(10.5, 3.6, 0.71, "VIRTUAL DYNAMIXEL", 0.21, GLOW, 600, 0.05)
    iso.led(9.4, 1.95, 0.71)
    # six TMC5160 modules with their heat sinks
    for i in range(6):
        y0 = 0.35 + i * 0.95
        iso.box(13.1, 14.9, y0, y0 + 0.75, 0, 0.3, "#14243c", "#0c182b", "#09121f", EDGE)
        iso.box(13.5, 14.5, y0 + 0.12, y0 + 0.63, 0.3, 0.55, "#3a4f6e", "#24354f", "#1c2a40")
    iso.text(14.0, 6.2, 0.01, "TMC5160 × 6", 0.24, "#6b7d99", 600, 0.04)


def usb_link(iso: Iso) -> None:
    """USB cable with Protocol 2.0 packets: a request to the board, a reply back."""
    p = iso.p
    cable = [p(4.2, 2.75, 0.3), p(5.0, 2.75, -0.3), p(6.4, 2.75, -0.3), p(7.0, 2.75, 0.22)]
    iso.path(cable, "#0e2a4f", 7)
    iso.path(cable, ACCENT, 2.2, ' opacity="0.9"')
    start, stop = p(4.5, 2.75, 0.6), p(6.8, 2.75, 0.6)
    track = f"M{start[0]:.1f},{start[1]:.1f} L{stop[0]:.1f},{stop[1]:.1f}"
    iso.text(5.6, 2.75, 1.05, "DYNAMIXEL 2.0", 0.24, "#9aabc4", 700, 0.04, face="y")
    for color, glow, motion, visible in (("#2f8cff", "#9cc8ff", "0;1;1;1", "0;1;1;0;0;0"),
                                         ("#3fcf8e", "#a6f0cb", "1;1;1;0", "0;0;0;1;1;0")):
        cubes = "".join(f'<rect x="{-11 + k * 8}" y="-3.5" width="6.5" height="6.5" rx="1.3" '
                        f'fill="{color}" stroke="{glow}" stroke-width="0.8" '
                        f'transform="skewY(30)"/>' for k in range(3))
        iso.parts.append(
            f'<g opacity="0" filter="url(#glow)">{cubes}'
            f'<animateMotion dur="4s" repeatCount="indefinite" path="{track}" '
            f'keyPoints="{motion}" keyTimes="0;0.35;0.55;1" calcMode="linear"/>'
            f'<animate attributeName="opacity" dur="4s" repeatCount="indefinite" '
            f'values="{visible}" keyTimes="0;0.05;0.33;0.4;0.95;1"/></g>')


def motor_cable(iso: Iso) -> None:
    """Motor cables from the drivers to the arm, with the step current as a glowing flow."""
    p = iso.p
    cable = [p(15.4, 3.2, 0.15), p(16.2, 3.2, -0.3), p(18.6, 3.2, -0.3), p(19.0, 3.2, 0.2)]
    iso.path(cable, "#0e2a4f", 9)
    iso.path(cable, ACCENT, 2.6, ' opacity="0.85"')
    iso.path(cable, "#9cc8ff", 2.4, ' class="flow-bus"')


# Poses of the real arm (joint values in rad, robot description joint names). The
# animation runs from START to STOP and back; FRAMES poses are rendered. The first pose is
# the static picture (PDF cover, reduced motion).
ARM_START = {"j1_base": -0.30, "j2_shoulder": 0.20, "j3_elbow": 0.75, "j4_forearm_roll": 0.0,
             "j5_wrist": 0.75, "gripper": 0.15}
ARM_STOP = {"j1_base": 0.35, "j2_shoulder": 0.45, "j3_elbow": 1.05, "j4_forearm_roll": 0.6,
            "j5_wrist": 0.35, "gripper": 1.20}
ARM_FRAMES = 14
ARM_PERIOD = 6.0     # s for one cycle there and back
ARM_AT = (20.7, 3.2, 0.0)


def moveo_arm(iso: Iso) -> str:
    """The real SmartManipulator-X arm from the robot description (hero_robot.py), on a
    plinth where the motor cables arrive. Returns the CSS of its animation."""
    iso.box(19.2, 22.2, 1.7, 4.7, -0.4, 0.0, MOTOR_TOP, MOTOR_LEFT, MOTOR_RIGHT, EDGE, 1.2)
    iso.led(22.2, 4.3, -0.2, r=2.4)
    place = Placement(*ARM_AT, yaw=-math.pi / 4, units=13.0, scale=iso.scale)
    groups, css, (x0, y0, x1, y1) = svg_frames(
        place, smooth_poses(ARM_FRAMES, ARM_START, ARM_STOP), ARM_PERIOD)
    iso.points += [(x0, y0), (x1, y1)]
    iso.parts.append(groups)
    return css


def hero() -> None:
    iso = Iso(scale=24.0)
    robot_pc(iso)
    usb_link(iso)
    controller_board(iso)
    motor_cable(iso)
    arm_css = moveo_arm(iso)
    path = os.path.join(OUT, "hero-3d.svg")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(iso.svg(HERO_LABEL, HERO_DEFS, HERO_STYLE + arm_css, glow_at=(12, 3.2)))
    print("wrote", os.path.relpath(path, os.getcwd()))


if __name__ == "__main__":
    hero()
