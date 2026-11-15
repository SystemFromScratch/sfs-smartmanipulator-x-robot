# System architecture

SmartManipulator-X has three parts: the Operator PC plans motions, the Robot
PC runs ROS 2 control and is the master of a DYNAMIXEL bus, and one doppelstep
drive per stepper motor answers on that bus as a DYNAMIXEL servo. This page
shows how they connect, who owns what, where the ROBOTIS software is reused,
and in which operating modes the system runs.

## Project objective

The target is to use the ROS 2 control and operator-software concepts of ROBOTIS [OpenMANIPULATOR-X](https://emanual.robotis.com/docs/en/platform/openmanipulator_x/overview/) with the mechanical design of [BCN3D Moveo](https://github.com/BCN3D/BCN3D-Moveo). Instead of DYNAMIXEL actuators, each stepper joint has a [doppelstep](../hardware/doppelstep.md) drive that answers on a DYNAMIXEL Protocol 2.0 bus as an XM430-W350 servo. The Robot PC, a Raspberry Pi CM4 on a [CM4-Duino](../hardware/cm4-duino/index.md) board, is the bus master and runs the unchanged ROBOTIS host software.

These sources have different roles. OpenMANIPULATOR-X is the reference for the ROS/DYNAMIXEL software stack; BCN3D Moveo is the mechanical reference. The OpenMANIPULATOR-X robot geometry, joints, actuator assumptions, and hardware configuration must not be copied as if they described Moveo.

> What is implemented today is on the [project status](../status.md) page.

## System context

![SmartManipulator-X system: Operator PC, Robot PC on the CM4-Duino, DYNAMIXEL bus, six doppelstep drives, gripper (separate project) and Moveo mechanics](images/system-architecture.svg)

Each doppelstep drive is a motor controller with its own device behavior (Control Table, motion profiles, current loop); it is not a protocol converter. Details of each link:

| Link | Implementation | Reference | State |
| --- | --- | --- | --- |
| Operator PC ↔ Robot PC | ROS 2 DDS (Fast DDS, UDPv4), `ROS_DOMAIN_ID` 42; Docker network `smx_net` in development, CM4 Wi-Fi on the robot | [Robot PC](../robot-pc/index.md), [Operator PC](../operator-pc/index.md) | Docker network: done. Wi-Fi: planned |
| Robot PC ↔ drives | DYNAMIXEL Protocol 2.0 bus from the CM4 PL011 UART0 (GPIO14/15) through a half-duplex interface | [DYNAMIXEL bus](../dynamixel/bus.md) | Planned |
| Drive ↔ motor | B-G431B-ESC1 power stage, shared-leg topology (legs U, V, W), current loop at 20 kHz, 16 microsteps, 24 V | [doppelstep drives](../hardware/doppelstep.md), [doppelstep hardware](https://systemfromscratch.com/sfs-doppelstep/hardware/) | Firmware done in simulation |
| Robot PC ↔ gripper | Virtual DYNAMIXEL on ID 7 with a PWM output to the MG996R | Separate project | Open |
| Power | 5 V for the CM4-Duino; separate 24 V motor supply for the drives; common ground star point | [DYNAMIXEL bus](../dynamixel/bus.md#power-and-ground) | Planned |

## Component ownership

| Component | Responsibility | Repository |
| --- | --- | --- |
| Robot PC | ROS 2 Jazzy, `ros2_control`, the ROBOTIS hardware path, bus master, robot bringup, canonical robot description, CM4-Duino deployment, this documentation | [sfs-smartmanipulator-x-robot](https://github.com/SystemFromScratch/sfs-smartmanipulator-x-robot) |
| Operator PC | MoveIt 2, RViz2, Gazebo, operator workflows, ROS 2 DDS client | [sfs-smartmanipulator-x-operator](https://github.com/SystemFromScratch/sfs-smartmanipulator-x-operator) |
| doppelstep | Stepper drive firmware: Protocol 2.0 device, XM430-W350 Control Table, motor control, protection, firmware update | [sfs-doppelstep](https://github.com/SystemFromScratch/sfs-doppelstep) |
| Gripper | Virtual DYNAMIXEL device on ID 7 driving the MG996R | Separate project (not started) |
| Bus interface hardware | Half-duplex interface between the CM4-Duino and the bus, power distribution | In this repository while it is a breadboard; its own hardware repository if it becomes a PCB |
| BCN3D Moveo | Mechanical links, joints, printed parts, assembly and mechanical limits | Upstream mechanical source; the project model (`smartmanipulator_x_description`) is generated from its CAD in this repository |
| ROBOTIS packages | SDK, hardware interface, messages, upstream OpenMANIPULATOR software | Upstream checkouts managed by `ros2_robot.repos` |

## Software reuse boundary

The physical control path is:

```text
MoveIt 2 (Operator PC)
  -> ROS 2 DDS
  -> ros2_control (Robot PC)
  -> ROBOTIS dynamixel_hardware_interface
  -> DynamixelSDK
  -> /dev/ttyDXL (CM4 PL011 UART0) -> half-duplex interface
  -> DYNAMIXEL bus: doppelstep IDs 1-6 (XM430-W350), gripper ID 7 (separate project)
  -> stepper motors / MG996R servo
```

Reuse the stock ROBOTIS hardware interface. doppelstep reports the real XM430-W350 model number (1020) and its Control Table, so no project-specific hardware interface and no custom model file are planned. What the Jazzy hardware interface actually reads and writes must still be checked against doppelstep in the [compatibility specification](../dynamixel/compatibility-spec.md) before it is relied on.

The bus carries only DYNAMIXEL packets. Protocol 2.0 is already a collision-free master/slave protocol, so no second link layer is added; that keeps DynamixelSDK, DYNAMIXEL Wizard and USB-to-DYNAMIXEL adapters usable on the bus.

Reusing the OpenMANIPULATOR-X ROS application does not make its robot model or joint/controller configuration valid for Moveo. MoveIt planning groups, joint names, limits, kinematics, transmission assumptions, `ros2_control` interfaces, and controller configuration must agree with the Moveo description and the physical stepper setup.

The Robot PC image is intentionally separate from the Operator PC runtime. MoveIt, RViz2, and Gazebo do not belong in the Robot PC image.

## Operating modes

| Mode | Hardware in `ros2_control` | Bus | State |
| --- | --- | --- | --- |
| Mock | `mock_components/GenericSystem` | – | Done |
| SIL | `dynamixel_hardware_interface` | Virtual bus joining doppelstep `native_sim` instances | Done ([tutorial](../tutorial-simulation.md)) |
| Bench | `dynamixel_hardware_interface` | One B-G431B-ESC1 over its ST-LINK virtual COM port | Planned (Stage 2) |
| Robot | `dynamixel_hardware_interface` | CM4-Duino UART0, six drives | Planned (Stages 3–4) |

The robot model and the joint names are identical in all modes.

## Operating assumptions

- The Robot PC software runs in Docker with ROS 2 Jazzy (Ubuntu 24.04 image); the host is Raspberry Pi OS on the CM4, or any Docker host during development.
- Only the Robot PC owns the bus. The Operator PC never connects to the drives.
- DDS domain ID, interface selection, discovery and firewall policy are configured consistently on both hosts. SSH is for administration, not the ROS data path.
- Positioning is open loop: no encoders, no limit switches, no homing yet. The arm is placed in the start pose by hand before power-up.
- Power-up order and an emergency stop are still open and must be defined before the full arm moves.

## Verified state versus target

The per-item state is kept on the [project status](../status.md) page. The [integration plan](../plan/doppelstep-cm4.md) lists the stages, their exit criteria and the decisions.

## Upstream references

- [ROBOTIS OpenMANIPULATOR-X overview](https://emanual.robotis.com/docs/en/platform/openmanipulator_x/overview/)
- [BCN3D Moveo source repository](https://github.com/BCN3D/BCN3D-Moveo)
- [ROBOTIS OpenMANIPULATOR ROS 2 source](https://github.com/ROBOTIS-GIT/open_manipulator)
- [DynamixelSDK source](https://github.com/ROBOTIS-GIT/DynamixelSDK)
- [DYNAMIXEL hardware interface source](https://github.com/ROBOTIS-GIT/dynamixel_hardware_interface)
- [doppelstep source](https://github.com/SystemFromScratch/sfs-doppelstep) and [documentation](https://systemfromscratch.com/sfs-doppelstep/)
