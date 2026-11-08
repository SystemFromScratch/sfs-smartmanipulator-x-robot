"""Generate smartmanipulator_x.urdf.xacro from geometry.json (and a plain test URDF)."""
import json
import sys

g = json.load(open(sys.argv[1]))
out_xacro, out_test = sys.argv[2], sys.argv[3]

mm = lambda v: " ".join(f"{x / 1000:.5f}".rstrip("0").rstrip(".") if x else "0" for x in v)
L = g["lengths_mm"]
gp = g["gripper_points_link5_mm"]
fo = g["finger_offsets_mm"]
ax = g["gear_axis_link5"]
GAXIS = "-1 0 0" if ax[0] < -0.99 else " ".join(str(round(a, 4)) for a in ax)
TOOL_Z = 0.150

PKG = "package://smartmanipulator_x_description/meshes"
# Light grey prints, dark hardware. Not orange: MoveIt draws its goal state in
# orange, and the robot must stay distinguishable from it in RViz.
COLOR = {"printed": "0.82 0.83 0.85 1.0", "hardware": "0.18 0.18 0.20 1.0"}


def link(name, visuals, collision=True, mass=0.2):
    v = "".join(f"""
    <visual>
      <geometry><mesh filename="{PKG}/visual/{name}_{kind}.stl" scale="1 1 1"/></geometry>
      <material name="smx_{kind}"><color rgba="{COLOR[kind]}"/></material>
    </visual>""" for kind in visuals)
    c = f"""
    <collision>
      <geometry><mesh filename="{PKG}/collision/{name}.stl" scale="1 1 1"/></geometry>
    </collision>""" if collision else ""
    return f"""
  <link name="{name}">{v}{c}
    <inertial>
      <mass value="{mass}"/>
      <inertia ixx="0.001" ixy="0" ixz="0" iyy="0.001" iyz="0" izz="0.001"/>
    </inertial>
  </link>
"""


def joint(name, jtype, parent, child, xyz, axis=None, limit=None, mimic=None, comment=None):
    s = f"\n  <!-- {comment} -->" if comment else ""
    s += f"""
  <joint name="{name}" type="{jtype}">
    <parent link="{parent}"/>
    <child link="{child}"/>
    <origin xyz="{xyz}" rpy="0 0 0"/>"""
    if axis:
        s += f'\n    <axis xyz="{axis}"/>'
    if limit:
        s += f'\n    <limit lower="{limit[0]}" upper="{limit[1]}" velocity="{limit[2]}" effort="{limit[3]}"/>'
    if mimic:
        s += f'\n    <mimic joint="{mimic[0]}" multiplier="{mimic[1]}" offset="0"/>'
    return s + "\n  </joint>\n"


PI = "3.14159"
HALF = "1.5708"
GRIP_MAX = "1.45"

body = ""
body += """
  <link name="world"/>
""" + joint("world_fixed", "fixed", "world", "base_link", "0 0 0")
body += link("base_link_placeholder", [], False)  # replaced below
body = body.replace(link("base_link_placeholder", [], False), "")
body += link("base_link", ["printed", "hardware"], mass=2.0).replace(
    'name="base_link">', 'name="base_link">').replace(f"{PKG}/visual/base_link_", f"{PKG}/visual/base_").replace(
    f"{PKG}/collision/base_link.stl", f"{PKG}/collision/base.stl")
body += "@EBOX@"
body += joint("j1_base", "revolute", "base_link", "link1", "0 0 0", "0 0 1", (f"${{-pi}}", "${pi}", 1.0, 10.0),
              comment="J1 base: rotation about the vertical axis")
body += link("link1", ["printed", "hardware"], mass=1.0)
body += joint("j2_shoulder", "revolute", "link1", "link2", mm([0, 0, L["j2_origin_z"][2]]), "0 1 0",
              (f"${{-pi/2}}", "${pi/2}", 1.0, 10.0),
              comment="J2 shoulder: two mirrored motors (DYNAMIXEL IDs 2 and 3); + tilts the arm forward")
body += link("link2", ["printed", "hardware"], mass=0.8)
body += joint("j3_elbow", "revolute", "link2", "link3", mm([0, 0, L["j3_origin"][2]]), "0 1 0",
              (f"${{-pi/2}}", "${pi/2}", 1.0, 10.0), comment="J3 elbow: + bends forward")
body += link("link3", ["printed", "hardware"], mass=0.4)
body += joint("j4_forearm_roll", "revolute", "link3", "link4", mm([0, 0, L["j4_origin"][2]]), "0 0 1",
              (f"${{-pi}}", "${pi}", 1.0, 5.0), comment="J4 forearm roll")
body += link("link4", ["printed", "hardware"], mass=0.3)
body += joint("j5_wrist", "revolute", "link4", "link5", mm([0, 0, L["j5_origin"][2]]), "0 1 0",
              (f"${{-pi/2}}", "${pi/2}", 1.0, 5.0), comment="J5 wrist pitch: + bends forward")
body += link("link5", ["printed", "hardware"], mass=0.2)

body += """
  <!--
    Gripper: the MG996R turns the servo gear (joint "gripper", DYNAMIXEL ID 7).
    The idler gear turns the other way; each finger hangs on a gear arm and a
    pivot arm of the same length (40 mm), a parallelogram, so the fingers keep
    their orientation. 0 = fully open (80 mm between the fingers), 1.45 rad = closed.
    Only "gripper" is commanded; the others are mimic joints.
  -->"""
body += joint("gripper", "revolute", "link5", "servo_gear", mm(gp["servo_gear"]), GAXIS,
              ("0", GRIP_MAX, 1.0, 2.0))
body += link("servo_gear", ["printed"], mass=0.02)
body += joint("gripper_idler_gear", "revolute", "link5", "idler_gear", mm(gp["idler_gear"]), GAXIS,
              ("-" + GRIP_MAX, "0", 1.0, 2.0), ("gripper", -1))
body += link("idler_gear", ["printed", "hardware"], mass=0.02)
body += joint("gripper_pivot_right", "revolute", "link5", "pivot_right", mm(gp["pivot_right"]), GAXIS,
              ("0", GRIP_MAX, 1.0, 2.0), ("gripper", 1))
body += link("pivot_right", ["hardware"], mass=0.01)
body += joint("gripper_pivot_left", "revolute", "link5", "pivot_left", mm(gp["pivot_left"]), GAXIS,
              ("-" + GRIP_MAX, "0", 1.0, 2.0), ("gripper", -1))
body += link("pivot_left", ["hardware"], mass=0.01)
body += joint("gripper_finger_right", "revolute", "servo_gear", "finger_right", mm(fo["right"]), GAXIS,
              ("-" + GRIP_MAX, "0", 1.0, 2.0), ("gripper", -1))
body += link("finger_right", ["printed", "hardware"], mass=0.02)
body += joint("gripper_finger_left", "revolute", "idler_gear", "finger_left", mm(fo["left"]), GAXIS,
              ("0", GRIP_MAX, 1.0, 2.0), ("gripper", 1))
body += link("finger_left", ["printed", "hardware"], mass=0.02)
body += joint("tool_fixed", "fixed", "link5", "tool_link", f"0 0 {TOOL_Z}",
              comment="Tool point between the fingertips of the closed gripper")
body += """
  <link name="tool_link"/>
"""

ebox = link("electronics_box", ["printed", "hardware"], mass=1.0).replace(
    f"{PKG}/visual/electronics_box_", f"{PKG}/visual/ebox_").replace(
    f"{PKG}/collision/electronics_box.stl", f"{PKG}/collision/ebox.stl") + joint(
    "electronics_box_fixed", "fixed", "base_link", "electronics_box", "0 0 0")

header = f"""<?xml version="1.0"?>
<!--
  SmartManipulator-X robot description: BCN3D Moveo mechanics.

  Generated from the BCN3D Moveo CAD assembly (STEP export of
  "BCN3D Moveo assembly.SLDASM", https://github.com/BCN3D/BCN3D-Moveo, MIT
  license, see meshes/LICENSE-BCN3D-Moveo). Joint axes come from the axles in
  the CAD; link meshes are the CAD parts of each link, decimated.

  Zero pose: arm straight up, gripper fully open. Positive J2, J3 and J5 bend
  the arm forward (+x); J1 and J4 turn counter-clockwise seen from the tip of
  their axis. Joint limits are placeholders until measured on the real arm.

  Do not edit by hand: regenerate with tools/cad (see docs/mechanical/index.md).
-->
<robot xmlns:xacro="http://www.ros.org/wiki/xacro" name="smartmanipulator_x">

  <xacro:arg name="use_mock_hardware" default="true"/>
  <!-- The electronics box of the original Moveo; off for the SmartFusion2 build. -->
  <xacro:arg name="electronics_box" default="false"/>
"""
footer = """
  <xacro:include filename="$(find smartmanipulator_x_description)/urdf/smartmanipulator_x.ros2_control.xacro"/>
  <xacro:smartmanipulator_x_ros2_control use_mock_hardware="$(arg use_mock_hardware)"/>

</robot>
"""
xacro = header + body.replace("@EBOX@", '\n  <xacro:if value="$(arg electronics_box)">' +
                              ebox.replace("\n  ", "\n    ") + "  </xacro:if>\n") + footer
open(out_xacro, "w").write(xacro)

test = ('<?xml version="1.0"?>\n<robot name="smx_test">\n' + header.split("<robot", 1)[1].split(">", 1)[1]
        .replace('<xacro:arg name="use_mock_hardware" default="true"/>', "")
        .replace('<xacro:arg name="electronics_box" default="false"/>', "")
        + body.replace("@EBOX@", ebox) + "\n</robot>\n")
test = test.replace("${-pi/2}", "-1.5708").replace("${pi/2}", "1.5708").replace("${-pi}", "-3.14159").replace("${pi}", "3.14159")
open(out_test, "w").write(test)
