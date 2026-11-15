# Overview

SmartManipulator-X is a robot arm project. It combines the ROS 2 control
and operator-software concepts of ROBOTIS
[OpenMANIPULATOR-X](https://emanual.robotis.com/docs/en/platform/openmanipulator_x/overview/)
with the mechanical design of [BCN3D Moveo](https://github.com/BCN3D/BCN3D-Moveo).
Instead of DYNAMIXEL actuators, every stepper joint of the Moveo has a
[doppelstep](hardware/doppelstep.md) drive that answers on a DYNAMIXEL
Protocol 2.0 bus as an XM430-W350 servo. The Robot PC, a Raspberry Pi
Compute Module 4 on a [CM4-Duino](hardware/cm4-duino/index.md) board, runs the
unchanged ROBOTIS host software as the bus master. The ROBOTIS stack can
then drive the arm as if it were built from DYNAMIXEL servos.

This documentation covers the whole system: the Robot PC and its board, the
DYNAMIXEL bus and the drives, the shared device contract, the Operator PC, and
the mechanics. It is published from the Robot PC repository and is the
starting point for all work on the project.

![SmartManipulator-X system: Operator PC, Robot PC on the CM4-Duino, DYNAMIXEL bus, six doppelstep drives, gripper and Moveo mechanics](architecture/images/system-architecture.svg)

## Open source and education

SmartManipulator-X is part of the [SystemFromScratch®](https://systemfromscratch.com/)
portfolio and is also built for teaching: from ROS 2 motion planning down to
the current loop of a stepper drive, every layer is visible and documented.
All parts are open source under the Apache License 2.0 — the Robot PC (this
repository), the Operator PC and the doppelstep drive firmware. Readers who
mainly want to work on algorithms start with the
[connection guide for beginners](beginners.md): the whole software stack runs
in simulation on one computer, and the hardware can be added step by step.

## System components

| Component | Role | Platform |
| --- | --- | --- |
| Operator PC | Motion planning and visualization (MoveIt 2, RViz2; Gazebo planned) | ROS 2 Jazzy in Docker, DDS client of the Robot PC |
| Robot PC | Robot-side ROS 2 control: `ros2_control`, the ROBOTIS hardware interface and DynamixelSDK; master of the DYNAMIXEL bus | Raspberry Pi CM4 (Wi-Fi) on a Waveshare CM4-Duino, ROS 2 Jazzy in Docker; any Docker host during development |
| DYNAMIXEL bus | Protocol 2.0 between the Robot PC and the drives | Single-wire half-duplex from the CM4 UART0 |
| doppelstep drives | One per stepper motor (IDs 1–6), XM430-W350 behavior, motor control and protection | ST B-G431B-ESC1 (STM32G431), Zephyr RTOS |
| Gripper | MG996R servo behind a virtual DYNAMIXEL device on ID 7 | Separate project, after the joint chain works |
| Mechanics | Joints, links and printed parts | BCN3D Moveo, NEMA 14/17/23 steppers |

## Repositories

| Repository | Content |
| --- | --- |
| [sfs-smartmanipulator-x-robot](https://github.com/SystemFromScratch/sfs-smartmanipulator-x-robot) | Robot PC Docker image and ROS 2 workspace, the robot description generated from the Moveo CAD, CM4-Duino deployment, diagnostics, and this documentation |
| [sfs-smartmanipulator-x-operator](https://github.com/SystemFromScratch/sfs-smartmanipulator-x-operator) | Operator PC: planning and visualization |
| [sfs-doppelstep](https://github.com/SystemFromScratch/sfs-doppelstep) | Stepper drive firmware that presents a motor as a DYNAMIXEL servo ([documentation](https://systemfromscratch.com/sfs-doppelstep/)) |
| [sfs-smartmanipulator-x-skills](https://github.com/SystemFromScratch/sfs-smartmanipulator-x-skills) | Engineering rules for coding agents, shared by all repositories of the project |

## Documentation map

| Section | Pages |
| --- | --- |
| **Guide** | [Getting started](getting-started.md): run the Robot PC in simulation and check it from a second host. [Connection guide for beginners](beginners.md): the system in pictures, in three levels. [Development](development.md): Docker, VS Code tasks, robot description, documentation, CI. [Project status](status.md): what works today. [Integration plan](plan/doppelstep-cm4.md): stages and decisions. |
| **Robot PC** | [Robot PC](robot-pc/index.md): ROS 2 control, Docker, network, joint contract. [Robot PC on the CM4-Duino](robot-pc/cm4-duino.md): deployment on the robot. [BCN3D Moveo mechanics](mechanical/index.md): the mechanical source and the generated robot model. |
| **System** | [System architecture](architecture/index.md): components, links, ownership, operating modes. [DYNAMIXEL bus](dynamixel/bus.md): topology, parameters, ID map, direction control. [DYNAMIXEL compatibility](dynamixel/compatibility-spec.md): the host/device contract. [Operator PC](operator-pc/index.md): planning, DDS. |
| **Hardware** | [CM4-Duino](hardware/cm4-duino/index.md): the Robot PC board, pinout, settings and links to the vendor files. [doppelstep drives](hardware/doppelstep.md): the joint drives. [Wiring](hardware/wiring.md): supplies, bus interface, drive connectors, joint motors. [Gripper servo](hardware/gripper-servo.md): MG996R and the gripper node. |

The whole documentation is also available as one PDF user manual (the PDF
button in the header of the website).

## Current status

In short (details on the [project status](status.md) page):

- **Done:** Robot PC image (amd64) with the ROBOTIS packages; simulation with
  mock hardware on a Docker network, checked by a smoke test and by the
  Operator PC container, whose commands arrive and are executed; robot
  description generated from the Moveo CAD; **SIL**: the Robot PC drives six
  simulated doppelstep drives over a virtual DYNAMIXEL bus with the real
  hardware interface, and MoveIt on the Operator PC plans and executes against
  it ([tutorial](tutorial-simulation.md)).
- **Next:** doppelstep changes for a shared bus (Fast Sync Read, Sync Read
  turn-taking, single-wire driver), then one drive on the bench, then the Robot
  PC on the CM4-Duino and the full arm.
- **Open:** single-wire bus interface, bus parameters, joint limits and
  directions on the real arm, emergency stop, gripper project.
