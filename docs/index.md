---
title: SmartManipulator-X — a ROS 2 robot arm on virtual DYNAMIXEL servos
description: A BCN3D Moveo arm driven by the unchanged ROBOTIS OpenMANIPULATOR-X ROS 2 stack, through a SmartFusion2 controller that answers as DYNAMIXEL servos.
template: home.html
hide:
  - navigation
  - toc
---

<span class="sfs-eyebrow">Quick start</span>

## The Robot PC in simulation, in two commands

No board and no arm are needed: the Robot PC runs `ros2_control` with mock
hardware in Docker, on a network that stands in for the Ethernet link to the
Operator PC. A second container on the same network checks it over ROS 2 DDS.

```bash
git clone https://github.com/SystemFromScratch/sfs-smartmanipulator-x-robot.git
cd sfs-smartmanipulator-x-robot

docker compose -f docker/docker-compose.yml up --build robot_pc                 # terminal 1: the Robot PC
docker compose -f docker/docker-compose.yml run --rm probe smx_smoke_test.sh    # terminal 2: a second host
```

The smoke test passes when it receives `/joint_states`, finds the
`joint_state_broadcaster`, `arm_controller` and `gripper_controller` active,
and `arm_controller` executes a short trajectory. In VS Code, **Ctrl+Shift+B**
offers the same steps as tasks ([Getting started](getting-started.md)).

## Find your way

| If you want to… | Read |
| --- | --- |
| Understand the system, its repositories and its current state | [Overview](overview.md) |
| Run the Robot PC and check it from a second host | [Getting started](getting-started.md) |
| Change the image, the workspace, the robot model or these docs | [Development](development.md) |
| Connect the Operator PC or the real controller board | [Robot PC](robot-pc/index.md) |
| See how the Robot PC, the firmware and the Operator PC fit together | [System architecture](architecture/index.md) |
| Check what the host expects from the virtual DYNAMIXEL devices | [DYNAMIXEL compatibility](dynamixel/compatibility-spec.md) |
| Build the controller firmware or test the axes | [Firmware](firmware/getting-started.md), [Motor tester GUI](gui/index.md) |
| Wire the Hello FPGA Kit, the TMC5160 drivers and the servo | [Hardware](hardware/wiring.md) |
| Read everything offline or print it | [PDF user manual](https://systemfromscratch.github.io/sfs-smartmanipulator-x-robot/downloads/SmartManipulator-X_User_Manual.pdf) |
