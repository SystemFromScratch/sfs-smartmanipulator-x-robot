<p align="center">
  <img src="docs/assets/images/hero-3d.svg" alt="A Robot PC running ROS 2 sends DYNAMIXEL packets over USB to a SmartFusion2 board with six TMC5160 drivers, which moves a BCN3D Moveo arm" width="720">
</p>

<h1 align="center">SmartManipulator-X</h1>

<p align="center">
  <b>A BCN3D Moveo arm driven by the unchanged ROBOTIS OpenMANIPULATOR-X ROS 2 stack, through a SmartFusion2 controller that answers as DYNAMIXEL servos.</b><br>
  ROS 2 Jazzy in Docker · ros2_control · DYNAMIXEL Protocol 2.0 · Zephyr on SmartFusion2
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
the mechanical design of [BCN3D Moveo](https://github.com/BCN3D/BCN3D-Moveo). A
SmartFusion2 controller replaces the DYNAMIXEL actuators: it drives the stepper motors
and the gripper servo and presents them to the ROS 2 host as virtual DYNAMIXEL devices
over Protocol 2.0, over USB CDC — not as a USB-to-DYNAMIXEL bridge.

This repository is the **Robot PC**: Ubuntu 24.04 with ROS 2 Jazzy in Docker, the project
ROS 2 packages, the robot description generated from the Moveo CAD, diagnostics, and the
documentation of the whole system.

| Component | Repository |
| --- | --- |
| Robot PC: ROS 2 control, robot description, documentation | this repository |
| Operator PC: MoveIt 2, RViz2, Gazebo | [sfs-smartmanipulator-x-operator](https://github.com/SystemFromScratch/sfs-smartmanipulator-x-operator) |
| Engineering rules for coding agents, shared by all repositories | [sfs-smartmanipulator-x-skills](https://github.com/SystemFromScratch/sfs-smartmanipulator-x-skills) |
| SmartFusion2 controller firmware and FPGA design | SmartManipulator-X-Controller, SmartManipulator-X-Libero |

## Project status

- [x] Robot PC image (ROS 2 Jazzy, ROBOTIS DYNAMIXEL SDK and hardware interface)
- [x] Simulation with mock hardware on a Docker network, smoke test from a second host
- [x] Robot description generated from the BCN3D Moveo CAD
- [ ] Joint limits measured on the arm (the URDF values are placeholders)
- [ ] Control Table, protocol behavior and timing verified against the ROBOTIS Jazzy sources ([compatibility specification](docs/dynamixel/compatibility-spec.md))
- [ ] Real-hardware `ros2_control` path (`robot.launch.py` refuses `use_mock_hardware:=false` until then)

## Quick start

Any computer with Docker and Docker Compose v2 (Windows with the WSL 2 backend works):

```bash
git clone https://github.com/SystemFromScratch/sfs-smartmanipulator-x-robot.git
cd sfs-smartmanipulator-x-robot

docker compose -f docker/docker-compose.yml up --build robot_pc                 # terminal 1: the Robot PC
docker compose -f docker/docker-compose.yml run --rm probe smx_smoke_test.sh    # terminal 2: a second host
```

The Compose file creates the network `smx_net` (`10.77.0.0/24`), which stands in for the
Ethernet link to the Operator PC. The smoke test passes when it receives `/joint_states`,
finds `joint_state_broadcaster`, `arm_controller` and `gripper_controller` active, and
`arm_controller` executes a short trajectory. Stop with **Ctrl+C** or
`docker compose -f docker/docker-compose.yml down`.

In VS Code, **Ctrl+Shift+B** offers *Robot PC: Start (mock hardware)*, *Stop*,
*Rebuild and restart*, *Build image*, *Rebuild image (no cache)* and
*Docs: Build PDF manual*; the smoke test is under **Tasks: Run Test Task**.

## Real hardware (Linux)

Connect the SmartFusion2 board and check that it enumerates (`ls -l /dev/ttyACM0`; set
`SMX_SERIAL_DEVICE` in `docker/.env` for another path, template `docker/env.example`).
Start a Robot PC shell with the device:

```bash
docker compose -f docker/docker-compose.yml -f docker/docker-compose.hw.yml run --rm robot_pc bash
```

The real-hardware `ros2_control` path is not configured yet; use this shell for device
diagnostics. Details: [Robot PC](docs/robot-pc/index.md).

## Project structure

```text
docker/                         Robot PC image, Compose services, DDS profile
ros2_ws/src/smartmanipulator_x/ bringup, config, description (from the Moveo CAD), tests
ros2_robot.repos                upstream ROBOTIS sources built into the image
tools/cad/                      STEP → URDF pipeline of the robot description
tools/diagnostics/              smoke test over DDS
tools/docs/                     PDF manual builder, hero illustration, Mermaid rendering
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
[avynohradov@systemfromscratch.com](mailto:avynohradov@systemfromscratch.com)

## License

Copyright © 2026 Anton Vynohradov. Project-owned files are licensed under the
[Apache License 2.0](LICENSE), matching the ROBOTIS OpenMANIPULATOR-X ROS 2 repository.
Third-party sources keep their own licenses: the ROBOTIS packages checked out through
`ros2_robot.repos`, and the BCN3D Moveo meshes (MIT,
`ros2_ws/src/smartmanipulator_x/smartmanipulator_x_description/meshes/LICENSE-BCN3D-Moveo`).

SystemFromScratch® is a registered trademark. The Apache License 2.0 grants no rights to
use the SystemFromScratch® name or logo; they may not be used to endorse or promote
products derived from SmartManipulator-X without prior written permission. ROBOTIS,
DYNAMIXEL and OpenMANIPULATOR are trademarks of ROBOTIS Co., Ltd.; SmartFusion2 is a
trademark of Microchip Technology Inc.; SmartManipulator-X is not affiliated with or
endorsed by them.
