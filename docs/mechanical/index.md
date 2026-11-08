# BCN3D Moveo Mechanics

## Mechanical source

The target arm mechanics are based on the [BCN3D Moveo project](https://github.com/BCN3D/BCN3D-Moveo), not on the OpenMANIPULATOR-X geometry. The upstream repository provides CAD files, STL files, assembly/user documentation, a bill of materials, and original firmware. Its README describes an educational, additively manufactured arm controlled by Arduino-based electronics.

This project replaces/adapts the control electronics; it does not claim that the original Moveo firmware or electronics are part of the SmartFusion2 control path. Refer to the upstream repository and its license for the authoritative mechanical files, assembly details, and attribution requirements.

## ROS model integration

The intended home for the project-owned ROS model is:

```text
ros2_ws/src/smartmanipulator_x/smartmanipulator_x_description/
```

The model in that package is generated from the BCN3D Moveo CAD: a STEP export of `BCN3D Moveo assembly.SLDASM` (upstream `CAD files/`, MIT license; the license text is in `meshes/LICENSE-BCN3D-Moveo`). The scripts in `tools/cad/` read the STEP, assign each part to a link, take the joint axes from the axles in the CAD, and write `urdf/smartmanipulator_x.urdf.xacro`, the decimated visual meshes, and convex-hull collision meshes. See `tools/cad/README.md` for the steps; `meshes/geometry.json` records the derived values.

| Quantity | From the CAD |
| --- | --- |
| Base (table plate top) to J2 axis | 231.64 mm |
| J2 to J3 | 221.12 mm |
| J3 to J5, along the J4 roll axis | 223.00 mm (J4 joint frame at 96.09 mm, where the wrist part begins) |
| Gripper | MG996R servo gear and idler gear with 40 mm arms, pivot arms of the same length: a parallelogram; 80 mm finger gap when open |

Conventions of the model:

- Zero pose: arm straight up, gripper fully open. The SmartFusion2 start pose (arm placed by hand before power-up) must match it, or the zero offsets must be set in the controller.
- Positive J2, J3 and J5 bend the arm forward (+x, away from the electronics box of the original Moveo); positive J1 and J4 turn counter-clockwise seen from the tip of their axis.
- `gripper` is the servo gear angle, 0 (open) to 1.45 rad (closed). The idler gear, pivot arms and fingers are mimic joints.
- The original electronics box is available with the xacro argument `electronics_box:=true`; it is off by default because this build uses other electronics.

Still to verify on the assembled arm: joint limits (the URDF values are placeholders), the direction of each motor against the conventions above, and any printed part changed for the NEMA 23 shoulder or the geared elbow motor.

When integrating the model:

- Use BCN3D Moveo geometry and assembly as the mechanical source of truth.
- Record the source revision and any project-specific changes to CAD/STL-derived geometry.
- Establish the base frame, link frames, joint axes, zero positions, and units from the source design and assembled robot.
- Verify joint ranges and collision geometry against the physical arm; do not inherit OpenMANIPULATOR-X limits or joint names.
- Define and document each Moveo joint-to-stepper mapping, transmission, microstepping, homing/reference method, and position scaling only after the hardware is selected and measured.
- Keep MoveIt planning groups, `ros2_control` joints, Gazebo joints, and physical motor mapping consistent.
- Preserve upstream license and attribution notices for imported or adapted assets. Do not assume that the project repository's license changes third-party asset licensing.

The electronics are selected in this repository: six BTT TMC5160T Pro drivers and the stepper motors per joint listed in [Axes and motors](../hardware/wiring.md#axes-and-motors) (J1 base, J2 shoulder with two motors, J3 elbow, J4 forearm roll, J5 wrist), plus an MG996R gripper servo; the joint-to-motor assignment is in `include/motor/motor_axes.h`. Joint naming in the ROS model, dimensions, limits, gear ratios and the sensing approach remain to be verified for the selected mechanical build. They are deliberately not inferred here from the project name.

## Acceptance checks

Before a model is treated as the canonical robot description, validate that it parses in URDF/Xacro tooling, has a connected link tree and correct joint types/axes, and produces a useful RViz visualization. Compare each joint range and frame placement with the assembled Moveo. Then check that the same joint contract can be loaded by both the physical `ros2_control` configuration and the selected Gazebo integration.