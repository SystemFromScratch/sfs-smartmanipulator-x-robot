# Getting started

This guide takes you from a fresh clone of the Robot PC repository to a
running Robot PC in simulation, checked from a second ROS 2 host. No
SmartFusion2 board and no arm are needed: `ros2_control` runs with mock
hardware, where every commanded joint position becomes the joint state at
once.

## Prerequisites

| Where | What |
| --- | --- |
| Simulation (any computer) | Git, Docker Engine or Docker Desktop (Windows with the WSL 2 backend works) and Docker Compose v2 |
| Real hardware | An Ubuntu 24.04 Robot PC (amd64 or arm64) and the controller board enumerated as USB CDC, typically `/dev/ttyACM0`. Docker Desktop on Windows does not expose a Linux `/dev/ttyACM0` |
| Optional | VS Code, which runs every step below as a task |

ROS 2 is not installed on the host: it comes with the Robot PC image
(`ros:jazzy-ros-base`).

## Clone

```bash
git clone https://github.com/SystemFromScratch/sfs-smartmanipulator-x-robot.git
cd sfs-smartmanipulator-x-robot
```

## Start the Robot PC

From the repository root:

```bash
docker compose -f docker/docker-compose.yml up --build robot_pc
```

The first run builds the image, which takes several minutes. The Compose file
creates the Docker network `smx_net` (`10.77.0.0/24`), which stands in for the
Ethernet link between the Robot PC and the Operator PC, and starts the Robot
PC container at `10.77.0.10`. It runs `robot_state_publisher`,
`ros2_control_node` with mock hardware, `joint_state_broadcaster`,
`arm_controller` and `gripper_controller`. The logs stay in the terminal.

## Check it from a second host

In a second terminal, start the `probe` container on the same network and run
the smoke test:

```bash
docker compose -f docker/docker-compose.yml run --rm probe smx_smoke_test.sh
```

The test passes when it receives `/joint_states`, finds
`joint_state_broadcaster`, `arm_controller` and `gripper_controller` active,
and `arm_controller` executes a short trajectory. For your own `ros2`
commands, open a shell on the probe instead:

```bash
docker compose -f docker/docker-compose.yml run --rm probe bash
ros2 topic list
```

Any other container on `smx_net` with the same `ROS_DOMAIN_ID` (default 42)
sees the Robot PC through ROS 2 DDS like a second machine on the LAN. To change
the domain, the subnet or the image tag, copy `docker/env.example` to
`docker/.env`.

## Stop and rebuild

Stop with **Ctrl+C** in the first terminal, or remove the containers and the
network:

```bash
docker compose -f docker/docker-compose.yml down
```

The workspace is built into the image, not mounted. After changing project
sources or `ros2_robot.repos`, start with `up --build` again.

## The same steps in VS Code

**Ctrl+Shift+B** opens the build task picker:

| Task | Does |
| --- | --- |
| **Robot PC: Start (mock hardware)** | `up --build robot_pc`; the logs stay in a dedicated terminal |
| **Robot PC: Stop** | `down`: removes the containers and `smx_net` |
| **Robot PC: Rebuild and restart** | Stop, then `up --build --force-recreate robot_pc` |
| **Robot PC: Build image** | Builds the image without starting it |
| **Robot PC: Rebuild image (no cache)** | Full rebuild, pulls the base image again |
| **Docs: Build PDF manual** | Writes the PDF user manual (see [Development](development.md#documentation)) |

The smoke test is under **Tasks: Run Test Task**, the probe shell and the
documentation preview under **Tasks: Run Task**.

## Next steps

- [Robot PC](robot-pc/index.md): the joint contract, how the Operator PC joins
  `smx_net`, and the hardware shell with the USB device.
- [Development](development.md): repository layout, the robot description
  generated from the CAD, documentation and CI.
- [System architecture](architecture/index.md): how the Robot PC, the
  controller firmware and the Operator PC fit together.
