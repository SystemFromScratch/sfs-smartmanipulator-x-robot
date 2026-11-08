# SmartManipulator-X

SmartManipulator-X combines the ROS control approach of ROBOTIS OpenMANIPULATOR-X with the mechanical design of [BCN3D Moveo](https://github.com/BCN3D/BCN3D-Moveo). A SmartFusion2-based controller is intended to replace the original actuator electronics and drive stepper motors while providing the verified DYNAMIXEL Protocol 2.0 behavior required by the ROS host stack. The target Robot PC is Ubuntu 24.04; its ROS environment is ROS 2 Jazzy in Docker.

The SmartFusion2 is intended to act as a virtual DYNAMIXEL device over USB CDC, not as a USB-to-DYNAMIXEL bridge. Control Table addresses, operating modes, timing, and device responses remain unverified until checked against current ROBOTIS sources.

## Repository layout

- `.agents/skills/`: governing project architecture and focused Robot PC, Operator PC, and SmartFusion2 guidance. The Operator PC skill is cross-repository guidance; its implementation lives in a separate repository.
- `docker/`: ROS 2 Jazzy Robot PC image, Compose service, and entrypoint.
- `ros2_ws/src/smartmanipulator_x/`: project-owned description, bringup, configuration, and test areas.
- `ros2_ws/src/robotis/`: checkout target for upstream repositories selected by `ros2_robot.repos` in the Robot PC image; `ros2.repos` remains the broader workspace manifest.
- SmartFusion2 firmware is maintained in a separate repository and is not included in this repository.
- `tools/`: diagnostics and USB utilities.
- `docs/`: the MkDocs site covering architecture, Moveo mechanics, Robot PC, Operator PC, SmartFusion2 firmware and hardware, DYNAMIXEL compatibility, and development. See [`docs/index.md`](docs/index.md).

Use the repository-local `.venv` for MkDocs (`requirements-docs.txt`). The VS Code task **Docs: Build PDF** (default build task) creates the `.venv` if needed and writes the PDF manual to `site/SmartManipulator-X.pdf`; by hand, run `python tools/docs/build_pdf.py`. **Docs: Live preview** runs `mkdocs serve`. The GitHub Pages deployment publishes the same PDF next to the site. Follow the platform-specific setup and Docker development workflow in the [development guide](docs/development/index.md); the [documentation home](docs/index.md) provides the site overview.

## Prerequisites

- Simulation (mock hardware): any computer with Docker Engine or Docker Desktop (Windows with the WSL 2 backend works) and Docker Compose v2.
- Real hardware: an Ubuntu 24.04 Linux Robot PC (arm64 or amd64) and the SmartFusion2 board enumerated as USB CDC, typically `/dev/ttyACM0`. Docker Desktop on Windows does not expose a Linux `/dev/ttyACM0` device.

## Robot PC in simulation on one computer

The Compose file creates the Docker network `smx_net` (`10.77.0.0/24`), which stands in for the Ethernet link between the Robot PC and the Operator PC. The Robot PC container (`10.77.0.10`) runs `robot_state_publisher`, `ros2_control` with mock hardware, and the controllers; any other container on `smx_net` with the same `ROS_DOMAIN_ID` (default 42; to change it, copy `docker/env.example` to `docker/.env`) sees it through ROS 2 DDS like a second machine on the LAN. From the repository root:

```bash
docker compose -f docker/docker-compose.yml up --build robot_pc      # terminal 1: the Robot PC
docker compose -f docker/docker-compose.yml run --rm probe smx_smoke_test.sh   # terminal 2: check from a second host
```

The smoke test passes when it receives `/joint_states`, finds `joint_state_broadcaster`, `arm_controller`, and `gripper_controller` active, and `arm_controller` executes a short trajectory. `run --rm probe bash` opens a shell on that second host for your own `ros2` commands. The same steps are VS Code tasks (**Robot PC: …**). Stop with **Ctrl+C** or `docker compose -f docker/docker-compose.yml down`.

The robot description is generated from the BCN3D Moveo CAD (link lengths, joint axes, meshes, gripper linkage; see `tools/cad/` and [BCN3D Moveo mechanics](docs/mechanical/index.md)); joint limits are still placeholders until measured on the arm. The details, including how the Operator PC joins `smx_net`, are in [Robot PC](docs/robot-pc/index.md).

## Robot PC with the SmartFusion2 (Linux)

Connect the SmartFusion2 to the Robot PC and check that Linux sees the USB CDC device:

```bash
lsusb
ls -l /dev/ttyACM0
```

If the board appears under another `/dev/ttyACM*` path, set `SMX_SERIAL_DEVICE` in `docker/.env` (template: `docker/env.example`). Check `ros2_robot.repos`; its `jazzy` refs are branch names and can move. The hardware override `docker/docker-compose.hw.yml` passes the device into the container. Start an interactive Robot PC shell with it:

```bash
docker compose -f docker/docker-compose.yml -f docker/docker-compose.hw.yml run --rm robot_pc bash
```

The container entrypoint sources ROS Jazzy and the built workspace automatically. Inside it, confirm the USB node and key ROS packages are visible:

```bash
ls -l /dev/ttyACM0
ros2 pkg list | grep -E '^(dynamixel_sdk|dynamixel_interfaces|dynamixel_hardware_interface|smartmanipulator_x_)'
```

Type `exit` to stop the interactive shell; `--rm` removes that container. The image uses `ros:jazzy-ros-base` and contains ROS control, the DYNAMIXEL SDK/interface, Robot PC packages, USB diagnostics, and build tools. It deliberately excludes MoveIt 2, RViz2, Gazebo, and the upstream OpenMANIPULATOR GUI/bringup packages. The workspace is baked into the image, not bind-mounted, so rebuild after changing project sources or `ros2_robot.repos`.

The real-hardware `ros2_control` path is not configured yet: `robot.launch.py` refuses `use_mock_hardware:=false`. Hardware operation is not yet validated: the Control Table, protocol behavior, timing, and final robot configuration remain to be verified in [`docs/dynamixel/compatibility-spec.md`](docs/dynamixel/compatibility-spec.md), and the joint limits of the robot description are placeholders until measured on the arm. Operator PC code and assets are maintained in a separate repository and are not included here.

## Development

See the [development guide](docs/development/index.md) for prerequisites, `.venv` setup, Docker image build/use, and the staged integration roadmap.

Project-owned files are licensed under Apache License 2.0, matching the ROBOTIS OpenMANIPULATOR-X ROS 2 repository. Third-party dependencies retain their own licenses; see [`LICENSE`](LICENSE).

No actuator addresses, operating modes, or compatibility claims are assumed by this scaffold; the 100 Hz controller rate in `controllers.yaml` is a starting value for mock hardware only.
