---
title: SmartManipulator-X — a ROS 2 robot arm on stepper drives that answer as DYNAMIXEL servos
description: A BCN3D Moveo arm driven by the unchanged ROBOTIS OpenMANIPULATOR-X ROS 2 stack, through doppelstep stepper drives that answer as DYNAMIXEL servos, with the Robot PC on a CM4-Duino.
template: home.html
hide:
  - navigation
  - toc
---

<span class="sfs-eyebrow">Quick start</span>

## The Robot PC in simulation, in two commands

No board and no arm are needed: the Robot PC runs `ros2_control` with mock
hardware in Docker, on a network that stands in for the Wi-Fi link to the
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
| Understand the system, its repositories and its current state | [Overview](overview.md), [Project status](status.md) |
| See what comes next and which decisions are made | [Integration plan](plan/doppelstep-cm4.md) |
| Work on robotics algorithms without knowing much electronics | [Connection guide for beginners](beginners.md) |
| Run the Robot PC and check it from a second host | [Getting started](getting-started.md) |
| Change the image, the workspace, the robot model or these docs | [Development](development.md) |
| Connect the Operator PC or a serial device to the Robot PC | [Robot PC](robot-pc/index.md) |
| Set up the Robot PC on the robot | [Robot PC on the CM4-Duino](robot-pc/cm4-duino.md), [CM4-Duino board](hardware/cm4-duino/index.md) |
| See how the Operator PC, the Robot PC and the drives fit together | [System architecture](architecture/index.md) |
| Wire the drives, the bus, the supplies and the gripper servo | [Wiring](hardware/wiring.md), [DYNAMIXEL bus](dynamixel/bus.md), [Gripper servo](hardware/gripper-servo.md) |
| Check what the host expects from the drives | [DYNAMIXEL compatibility](dynamixel/compatibility-spec.md) |
| Read everything offline or print it | [PDF user manual](https://systemfromscratch.github.io/sfs-smartmanipulator-x-robot/downloads/SmartManipulator-X_User_Manual.pdf) |
