<p align="center">
  <img src="docs/assets/images/hero-3d.svg" alt="A Robot PC running ROS 2 sends DYNAMIXEL packets to six doppelstep stepper drives, which move a BCN3D Moveo arm" width="720">
</p>

<h1 align="center">SmartManipulator-X</h1>

<p align="center">
  <b>A BCN3D Moveo arm driven by the unchanged ROBOTIS OpenMANIPULATOR-X ROS 2 stack, through doppelstep stepper drives that answer as DYNAMIXEL servos.</b><br>
  ROS 2 Jazzy in Docker · ros2_control · DYNAMIXEL Protocol 2.0 · Raspberry Pi CM4 (CM4-Duino)
</p>

<p align="center">
  <a href="https://github.com/SystemFromScratch/sfs-smartmanipulator-x-robot/actions/workflows/docker-publish.yml"><img src="https://github.com/SystemFromScratch/sfs-smartmanipulator-x-robot/actions/workflows/docker-publish.yml/badge.svg" alt="Robot PC image"></a>
  <a href="https://github.com/SystemFromScratch/sfs-smartmanipulator-x-robot/actions/workflows/documentation.yml"><img src="https://github.com/SystemFromScratch/sfs-smartmanipulator-x-robot/actions/workflows/documentation.yml/badge.svg" alt="Documentation"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0-blue.svg" alt="License: Apache-2.0"></a>
</p>

<p align="center">
  <a href="https://systemfromscratch.github.io/sfs-smartmanipulator-x-robot/">Documentation</a> ·
  <a href="https://systemfromscratch.github.io/sfs-smartmanipulator-x-robot/downloads/SmartManipulator-X_User_Manual.pdf">PDF manual</a> ·
  <a href="https://systemfromscratch.github.io/sfs-smartmanipulator-x-robot/getting-started/">Getting started</a>
</p>

---

## Overview

SmartManipulator-X combines the ROS 2 control approach of ROBOTIS OpenMANIPULATOR-X with
the mechanical design of [BCN3D Moveo](https://github.com/BCN3D/BCN3D-Moveo). Every
stepper joint has a [doppelstep](https://github.com/SystemFromScratch/sfs-doppelstep)
drive that answers on a DYNAMIXEL Protocol 2.0 bus as an XM430-W350 servo, so the stock
ROBOTIS hardware interface is meant to drive the arm without project-specific code. On
the robot, the Robot PC will be a Raspberry Pi Compute Module 4 on a Waveshare CM4-Duino
board that reaches the Operator PC over Wi-Fi.

This repository is the **Robot PC**: ROS 2 Jazzy in Docker, the project ROS 2 packages,
the robot description generated from the Moveo CAD, the CM4-Duino deployment,
diagnostics, and the documentation of the whole system.

SmartManipulator-X is part of the [SystemFromScratch®](https://systemfromscratch.com/)
portfolio and is also meant for education. **All parts are open source** (Apache-2.0):
the Robot PC, the Operator PC and the doppelstep drive firmware. New to electronics but
interested in robotics algorithms? Start with the
[connection guide for beginners](docs/beginners.md): level 1 needs only a computer with
Docker.

| Component | Repository |
| --- | --- |
| Robot PC: ROS 2 control, robot description, CM4-Duino deployment, documentation | this repository |
| Operator PC: MoveIt 2, RViz2 | [sfs-smartmanipulator-x-operator](https://github.com/SystemFromScratch/sfs-smartmanipulator-x-operator) |
| Joint drives: stepper drive firmware that answers as a DYNAMIXEL servo | [sfs-doppelstep](https://github.com/SystemFromScratch/sfs-doppelstep) |
| Engineering rules for coding agents, shared by all repositories | [sfs-smartmanipulator-x-skills](https://github.com/SystemFromScratch/sfs-smartmanipulator-x-skills) |

## Project status

Full table: [Project status](docs/status.md). Next steps and decisions:
[integration plan](docs/plan/doppelstep-cm4.md).

- [x] Robot PC image (ROS 2 Jazzy, ROBOTIS DYNAMIXEL SDK and hardware interface), amd64
- [x] Simulation with mock hardware on a Docker network; smoke test and Operator PC container connected over DDS
- [x] Robot description generated from the BCN3D Moveo CAD
- [x] CM4-Duino documented, vendor files archived
- [ ] Robot PC ↔ doppelstep in simulation (SIL), real-hardware `ros2_control` path
- [ ] One doppelstep drive on the bench (ST-LINK virtual COM port)
- [ ] Robot PC on the CM4-Duino (arm64 image, deployment, DYNAMIXEL bus, Wi-Fi)
- [ ] Full arm: six drives, joint limits measured, emergency stop
- [ ] Gripper as a separate project (virtual DYNAMIXEL on ID 7)

## Quick start

Any computer with Docker and Docker Compose v2 (Windows with the WSL 2 backend works):

```bash
git clone https://github.com/SystemFromScratch/sfs-smartmanipulator-x-robot.git
cd sfs-smartmanipulator-x-robot

docker compose -f docker/docker-compose.yml up --build robot_pc                 # terminal 1: the Robot PC
docker compose -f docker/docker-compose.yml run --rm probe smx_smoke_test.sh    # terminal 2: a second host
```

The Compose file creates the network `smx_net` (`10.77.0.0/24`), which stands in for the
network link (Wi-Fi on the robot) to the Operator PC. The smoke test passes when it receives `/joint_states`,
finds `joint_state_broadcaster`, `arm_controller` and `gripper_controller` active, and
`arm_controller` executes a short trajectory. Stop with **Ctrl+C** or
`docker compose -f docker/docker-compose.yml down`.

In VS Code, **Ctrl+Shift+B** offers *Robot PC: Start (mock hardware)*, *Stop*,
*Rebuild and restart*, *Build image*, *Rebuild image (no cache)* and
*Docs: Build PDF manual*; the smoke test is under **Tasks: Run Test Task**.

## Real hardware

Not usable yet: the real-hardware `ros2_control` path is the next stage of the
[integration plan](docs/plan/doppelstep-cm4.md). For device diagnostics on a Linux host,
set `SMX_SERIAL_DEVICE` in `docker/.env` (template `docker/env.example`) and start a
Robot PC shell with the device:

```bash
docker compose -f docker/docker-compose.yml -f docker/docker-compose.hw.yml run --rm robot_pc bash
```

Details: [Robot PC](docs/robot-pc/index.md), [DYNAMIXEL bus](docs/dynamixel/bus.md),
[CM4-Duino](docs/hardware/cm4-duino/index.md).

## Project structure

```text
docker/                         Robot PC image, Compose services, DDS profile
ros2_ws/src/smartmanipulator_x/ bringup, config, description (from the Moveo CAD), tests
ros2_robot.repos                upstream ROBOTIS sources built into the image
deploy/cm4-duino/               CM4-Duino deployment files (planned)
tools/cad/                      STEP → URDF pipeline of the robot description
tools/diagnostics/              smoke test over DDS
tools/docs/                     PDF manual builder, hero illustration, diagram generators
docs/, overrides/, mkdocs.yml   documentation (website and PDF manual)
```

## Documentation

The website and the PDF user manual are built from `docs/` and published by CI to
[GitHub Pages](https://systemfromscratch.github.io/sfs-smartmanipulator-x-robot/).
Locally, in the repository `.venv` (`pip install -r requirements-docs.txt`; WeasyPrint
needs Pango):

```bash
python -m mkdocs serve                  # live preview
python tools/docs/build_manual.py       # build/manual/SmartManipulator-X_User_Manual_v<version>.pdf
```

See [Development](docs/development.md) for the details.

## Author

**Anton Vynohradov** — Embedded Systems Engineer · Founder of SystemFromScratch®

[systemfromscratch.com](https://systemfromscratch.com) ·
[GitHub](https://github.com/AntonVynohradov) ·
[LinkedIn](https://www.linkedin.com/in/vynohradov) ·
[ORCID 0009-0005-6965-0911](https://orcid.org/0009-0005-6965-0911) ·
[contact@systemfromscratch.com](mailto:contact@systemfromscratch.com)

## License

Copyright © 2026 Anton Vynohradov. Project-owned files are licensed under the
[Apache License 2.0](LICENSE), matching the ROBOTIS OpenMANIPULATOR-X ROS 2 repository.
Third-party sources keep their own licenses: the ROBOTIS packages checked out through
`ros2_robot.repos`, and the BCN3D Moveo meshes (MIT,
`ros2_ws/src/smartmanipulator_x/smartmanipulator_x_description/meshes/LICENSE-BCN3D-Moveo`).

SystemFromScratch® is a registered trademark. The Apache License 2.0 grants no rights to
use the SystemFromScratch® name or logo; they may not be used to endorse or promote
products derived from SmartManipulator-X without prior written permission. ROBOTIS,
DYNAMIXEL and OpenMANIPULATOR are trademarks of ROBOTIS Co., Ltd. Raspberry Pi is a
trademark of Raspberry Pi Ltd. Waveshare is a trademark of Waveshare Electronics. STM32
is a registered trademark of STMicroelectronics International N.V. ROS is a trademark of
Open Source Robotics Foundation, Inc. BCN3D is a trademark of BCN3D Technologies.
SmartManipulator-X is not affiliated with or endorsed by these companies.

Third-party documents are kept only as backup copies and are not covered by the Apache
License 2.0: the Waveshare files in `docs/hardware/cm4-duino/vendor/` (© Waveshare, a
discontinued board) and the datasheets in `docs/hardware/datasheets/` (© their
publishers). They are not published on the documentation website, which links to the
originals on the publishers' websites.
