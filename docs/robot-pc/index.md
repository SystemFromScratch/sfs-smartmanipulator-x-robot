# Robot PC

## Responsibility

The Robot PC owns the real-time-facing ROS 2 control path and is the only computer that connects directly to the SmartFusion2 USB CDC device:

```text
ros2_control
  -> ROBOTIS dynamixel_hardware_interface
  -> DynamixelSDK
  -> USB CDC (commonly /dev/ttyACM0)
  -> SmartFusion2
  -> stepper motor control
```

The stock ROBOTIS hardware interface is the preferred starting point, but it must not be assumed compatible until the exact protocol and control-table accesses have been checked against current Jazzy source. See the [compatibility specification](../dynamixel/compatibility-spec.md).

## Host and container

The target Robot PC host is Ubuntu 24.04 with Docker Engine and Docker Compose. The paths below (`docker/`, `ros2_ws/`, `ros2_robot.repos`) are in the **Robot PC repository**, not in this firmware repository. Its current `docker/` profile is based on `ros:jazzy-ros-base`. It imports the DYNAMIXEL SDK/interface dependencies through `ros2_robot.repos` and builds the project-owned packages; `docker-compose.hw.yml` maps `/dev/ttyACM0` into the container with the `dialout` group.

MoveIt 2, RViz2, Gazebo, and the Operator PC application are intentionally excluded from this image. The Operator PC owns those dependencies and connects over ROS 2 DDS.

## Simulation on one computer

Until the hardware path is verified, the Robot PC runs with `mock_components/GenericSystem`: the commanded joint position becomes the state at once, so the whole ROS side (DDS, controllers, MoveIt on the Operator PC) can be developed without the SmartFusion2. Everything runs in containers on one computer; a Docker network replaces the Ethernet cable:

```text
 one computer (Docker)
 ┌─────────────────────────────── smx_net 10.77.0.0/24 ───────────────────────────────┐
 │                                                                                    │
 │ robot_pc 10.77.0.10         probe (dynamic IP)      Operator PC container          │
 │ robot_state_publisher       ros2 CLI                MoveIt 2, RViz2                │
 │ ros2_control_node (mock)    smx_smoke_test.sh       (Operator PC repo)             │
 │ joint_state_broadcaster                                                            │
 │ arm_controller                                                                     │
 │ gripper_controller                                                                 │
 └──────────────────────── ROS 2 DDS, UDPv4, ROS_DOMAIN_ID=42 ────────────────────────┘
```

From the Robot PC repository root:

```bash
docker compose -f docker/docker-compose.yml up --build robot_pc                 # Robot PC
docker compose -f docker/docker-compose.yml run --rm probe smx_smoke_test.sh    # second host
```

| File | Role |
| --- | --- |
| `docker/docker-compose.yml` | `robot_pc` service (mock hardware by default), `probe` service (profile `tools`), network `smx_net` |
| `docker/docker-compose.hw.yml` | Override that passes the controller's USB device (Linux hosts) |
| `docker/env.example` | Template for `docker/.env`: `ROS_DOMAIN_ID`, subnet, Robot PC address, image tag, serial device |
| `docker/dds/fastdds_udp.xml` | Fast DDS profile: UDPv4 only, no shared memory between containers |
| `smartmanipulator_x_bringup/launch/robot.launch.py` | `robot_state_publisher`, `ros2_control_node`, controller spawner |
| `smartmanipulator_x_config/config/controllers.yaml` | `joint_state_broadcaster`, `arm_controller` (J1–J5), `gripper_controller`, 100 Hz |
| `smartmanipulator_x_description/` | Moveo model generated from the BCN3D CAD (`tools/cad/`) and its `ros2_control` block |
| `tools/diagnostics/smx_smoke_test.sh` | Discovery, controller state, and trajectory check from another host |

### Joint contract

The Operator PC, the simulation, and the real hardware must use the same joint names. These are defined in `smartmanipulator_x_description`:

| Joint | Moveo axis | DYNAMIXEL ID (SmartFusion2) | Controller |
| --- | --- | --- | --- |
| `j1_base` | J1 base | 1 | `arm_controller` |
| `j2_shoulder` | J2 shoulder | 2 and 3 (two mirrored motors) | `arm_controller` |
| `j3_elbow` | J3 elbow | 4 | `arm_controller` |
| `j4_forearm_roll` | J4 forearm roll | 5 | `arm_controller` |
| `j5_wrist` | J5 wrist | 6 | `arm_controller` |
| `gripper` | gripper servo | 7 | `gripper_controller` |

Lengths, joint axes, and meshes come from the BCN3D Moveo CAD ([BCN3D Moveo mechanics](../mechanical/index.md)); joint limits are placeholders until measured on the arm. The gripper also has mimic joints (`gripper_idler_gear`, `gripper_pivot_*`, `gripper_finger_*`) that follow `gripper`; they are not in `ros2_control`. On the real robot, `dynamixel_hardware_interface` can map the two shoulder motors onto one joint with its `transmission_to_joint_matrix` and `joint_to_transmission_matrix` parameters; this is still to be configured and verified.

### Operator PC on the same network

The Operator PC container joins the network by name. In its Compose file:

```yaml
services:
  operator_pc:
    environment:
      ROS_DOMAIN_ID: "42"
      RMW_IMPLEMENTATION: rmw_fastrtps_cpp
      FASTDDS_DEFAULT_PROFILES_FILE: /etc/smx/fastdds_udp.xml  # copy of docker/dds/fastdds_udp.xml
    networks: [smx_net]
networks:
  smx_net:
    external: true
```

Start the Robot PC first; it creates `smx_net`. On Windows, run the Operator PC container from a WSL 2 distribution so RViz2 can use WSLg (mount `/tmp/.X11-unix` and `/mnt/wslg`, pass `DISPLAY`, `WAYLAND_DISPLAY`, and `XDG_RUNTIME_DIR`). ROS 2 installed natively on Windows does not discover containers on `smx_net`: Docker Desktop does not route multicast between the host and its container networks.

### Moving to another Robot PC

The image has no host-specific state. On a Raspberry Pi CM4 or a Jetson (both arm64, Ubuntu 24.04), build it there or pull a multi-architecture image, and replace `smx_net` by the real Ethernet: drop the `networks` entries and use `network_mode: host`. `ROS_DOMAIN_ID` and the Fast DDS profile stay the same.

## Hardware shell

Build and start an interactive Robot PC shell with the USB device from the Robot PC repository root:

```bash
docker compose -f docker/docker-compose.yml -f docker/docker-compose.hw.yml run --rm robot_pc bash
```

Before starting, connect the board and confirm the device path on the Linux host. The kit appears through its MCP2221A USB-UART; the host must open it at 460800 bps and send `&` once before the first DYNAMIXEL packet (see [Host link](../hardware/wiring.md#host-link-usb-pic32-smartfusion2)):

```bash
lsusb
ls -l /dev/ttyACM0
```

If the board enumerates under another `/dev/ttyACM*` path, set `SMX_SERIAL_DEVICE` in `docker/.env` (template: `docker/env.example`). Ensure the host user and container have appropriate device permissions. Windows does not expose a Linux `/dev/ttyACM0` device directly to this container configuration.

Inside the container, inspect the available packages with:

```bash
ros2 pkg list | grep -E '^(dynamixel_sdk|dynamixel_interfaces|dynamixel_hardware_interface|smartmanipulator_x_)'
```

`robot.launch.py` refuses `use_mock_hardware:=false` until the real-hardware `ros2_control` configuration is verified. No physical bringup or SmartFusion2 hardware operation is documented as validated.

## Network and operation

The Robot PC communicates with the Operator PC using ROS 2 DDS over the configured network. Configure the same `ROS_DOMAIN_ID` on both computers and validate DDS discovery, selected network interfaces, multicast/unicast policy, and firewall behavior on the actual network. Do not use SSH as the ROS transport.

Do not enable motor motion until the actuator mapping, motor-driver configuration, limits, homing behavior, and an appropriate stop/safety procedure have been reviewed on the assembled robot. Test incrementally: upstream ROS without hardware, USB/device communication, one virtual actuator, one physical axis, then the complete mechanism.

## Repository ownership

- Robot PC Docker and bringup: `docker/` and `ros2_ws/src/smartmanipulator_x/smartmanipulator_x_bringup/`.
- Project controller and hardware configuration: `ros2_ws/src/smartmanipulator_x/smartmanipulator_x_config/`.
- Canonical robot description location: `ros2_ws/src/smartmanipulator_x/smartmanipulator_x_description/`.
- Upstream dependencies: separate source checkouts selected by `ros2_robot.repos`; pin immutable revisions for reproducible builds before production use.