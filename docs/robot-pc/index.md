# Robot PC

## Responsibility

The Robot PC owns the real-time-facing ROS 2 control path and is the only computer connected to the [DYNAMIXEL bus](../dynamixel/bus.md):

```text
ros2_control
  -> ROBOTIS dynamixel_hardware_interface
  -> DynamixelSDK
  -> /dev/ttyDXL (CM4 UART0 on the robot; virtual bus or USB serial port during development)
  -> doppelstep drives, IDs 1-6
  -> stepper motors
```

The stock ROBOTIS hardware interface is the intended path, but it must not be assumed compatible until the protocol and Control Table accesses have been checked against the current Jazzy source and doppelstep. See the [compatibility specification](../dynamixel/compatibility-spec.md). On the robot the Robot PC is a CM4 on the CM4-Duino board, see [Robot PC on the CM4-Duino](cm4-duino.md).

## Host and container

The Robot PC runs in Docker on any host with Docker Engine and Docker Compose v2; on the robot that host is Raspberry Pi OS on the CM4. The paths below (`docker/`, `ros2_ws/`, `ros2_robot.repos`) are in this repository. The current `docker/` profile is based on `ros:jazzy-ros-base`. It imports the DYNAMIXEL SDK/interface dependencies through `ros2_robot.repos` and builds the project-owned packages; `docker-compose.hw.yml` maps a serial device (`SMX_SERIAL_DEVICE`) into the container with the `dialout` group.

MoveIt 2, RViz2, Gazebo, and the Operator PC application are intentionally excluded from this image. The Operator PC owns those dependencies and connects over ROS 2 DDS.

## Simulation on one computer

Until the hardware path is verified, the Robot PC runs with `mock_components/GenericSystem`: the commanded joint position becomes the state at once, so the whole ROS side (DDS, controllers, MoveIt on the Operator PC) can be developed without any drive. Everything runs in containers on one computer; a Docker network replaces the Wi-Fi link:

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

From the repository root (the [getting started](../getting-started.md) guide walks through it):

```bash
docker compose -f docker/docker-compose.yml up --build robot_pc                 # Robot PC
docker compose -f docker/docker-compose.yml run --rm probe smx_smoke_test.sh    # second host
```

| File | Role |
| --- | --- |
| `docker/docker-compose.yml` | `robot_pc` service (mock hardware by default), `probe` service (profile `tools`), network `smx_net` |
| `docker/docker-compose.sil.yml` | Override for the SIL setup: virtual DYNAMIXEL bus to simulated doppelstep drives, `hardware:=sil` |
| `docker/docker-compose.hw.yml` | Override that passes a serial device into the container (Linux hosts) |
| `docker/env.example` | Template for `docker/.env`: `ROS_DOMAIN_ID`, subnet, Robot PC address, image tag, serial device |
| `docker/dds/fastdds_udp.xml` | Fast DDS profile: UDPv4 only, no shared memory between containers |
| `smartmanipulator_x_bringup/launch/robot.launch.py` | `robot_state_publisher`, `ros2_control_node`, controller spawner; `hardware:=mock` (default), `sil` or `real` (refused until the bench stage) |
| `smartmanipulator_x_config/config/controllers.yaml` | `joint_state_broadcaster`, `arm_controller` (J1–J5), `gripper_controller`, 100 Hz |
| `smartmanipulator_x_description/` | Moveo model generated from the BCN3D CAD (`tools/cad/`) and its `ros2_control` block |
| `tools/diagnostics/smx_smoke_test.sh` | Discovery, controller state, and trajectory check from another host |
| `tools/sim/smx_dxl_bus.py`, `tools/sim/smx_sil_start.sh`, `tools/sim/smx_bus_timing.py` | Virtual DYNAMIXEL bus, start script of the SIL setup, bus timing diagnostics |

### Joint contract

The Operator PC, the simulation, and the real hardware must use the same joint names. These are defined in `smartmanipulator_x_description`:

| Joint | Moveo axis | DYNAMIXEL ID | Controller |
| --- | --- | --- | --- |
| `j1_base` | J1 base | 1 | `arm_controller` |
| `j2_shoulder` | J2 shoulder | 2 and 3 (two mirrored motors) | `arm_controller` |
| `j3_elbow` | J3 elbow | 4 | `arm_controller` |
| `j4_forearm_roll` | J4 forearm roll | 5 | `arm_controller` |
| `j5_wrist` | J5 wrist | 6 | `arm_controller` |
| `gripper` | gripper servo (separate project; mock until then) | 7 | `gripper_controller` |

Lengths, joint axes, and meshes come from the BCN3D Moveo CAD ([BCN3D Moveo mechanics](../mechanical/index.md)); joint limits are placeholders until measured on the arm. The gripper also has mimic joints (`gripper_idler_gear`, `gripper_pivot_*`, `gripper_finger_*`) that follow `gripper`; they are not in `ros2_control`. On the real robot, `dynamixel_hardware_interface` can map the two shoulder motors onto one joint with its `transmission_to_joint_matrix` and `joint_to_transmission_matrix` parameters; this is still to be configured and verified.

### SIL: simulated doppelstep drives

> **Status (2026-11-15):** works end to end with six doppelstep `native_sim` drives;
> `smx_smoke_test.sh` passes, without read timeouts since SIL run 8. Findings of all runs
> are in the [compatibility specification](../dynamixel/compatibility-spec.md#sil-run-8-2026-11-15-pass-no-read-timeouts). Stage 1 of the [integration plan](../plan/doppelstep-cm4.md#stage-1-sil-on-the-pc-no-hardware).

New to SIL? Follow the [step-by-step tutorial](sil-tutorial.md).

In the SIL setup (software in the loop) the Robot PC uses its real hardware path,
`dynamixel_hardware_interface` and DynamixelSDK, but the drives are the doppelstep
firmware running on the PC as Zephyr `native_sim`. A small tool joins them into one
virtual DYNAMIXEL bus:

```text
 robot_pc container                                     Docker host (Linux or WSL 2)
 ros2_control -> DynamixelSDK -> /dev/ttyDXL (pty)
                                  smx_dxl_bus.py  ── TCP 5555 ──> doppelstep native_sim (ID 1)
                                                  ── TCP 5556 ──> doppelstep native_sim (ID 2)
                                                  ...         ──> ... (ID 6)
```

- Every byte the host sends goes to all drives; only the addressed drive answers,
  as on the shared wire. What a drive sends also reaches the other drives: Fast
  Sync Read, which the hardware interface uses, needs it, because the drives build
  one common answer packet in turn. The host does not receive an echo of its own
  packets, like with the bus interface of the CM4-Duino.
- Fast Sync Read and Fast Bulk Read are dropped by default: doppelstep answers them
  only for its own ID, so six drives would send six packets where the host expects
  one. Without an answer the ROBOTIS interface falls back to normal Sync Read after
  10 attempts (expect ten `FastSyncRead TxRx failed` lines at start). See the
  [compatibility specification](../dynamixel/compatibility-spec.md#sil-run-2-2026-11-15).
- Answers to Sync Read and Bulk Read reach the host in the order of the request, as on
  a real bus where each device waits for its turn; the simulated drives answer at once
  ([SIL run 3](../dynamixel/compatibility-spec.md#sil-run-3-2026-11-15)).
- `smx_bus_timing.py` measures PING and Sync Read answer times on the bus, for
  diagnosing timeouts.
- Timing: a simulated drive polls its serial port every 10 ms, so a Sync Read of six
  drives takes up to about 25 ms instead of well under 1 ms. In the control loop the
  hardware interface waits for an answer for one control period only
  (`setPacketTimeout(period_ms)`), so SIL runs the controllers at **25 Hz**
  (`SMX_UPDATE_RATE`, period 40 ms); at 50 Hz a few Sync Reads per second timed out
  ([SIL run 8](../dynamixel/compatibility-spec.md#sil-run-8-2026-11-15-pass-no-read-timeouts)).
  `baud_rate` 9600 (`SMX_BAUD_RATE`) only lengthens the DynamixelSDK timeout of the
  reads at start; the virtual bus ignores the baud rate. The bus reports each
  incomplete read (`read incomplete: missing ID …`) and a timing summary every 10 s.
  The communication error timeout of the interface is 5 s in SIL (500 ms otherwise),
  long enough for the 10 Fast Sync Read attempts before the fallback. The real bus
  keeps 100 Hz and 1 Mbps.
- The simulated drives keep running between Robot PC starts. If a run was killed, they
  may still have torque on; in SIL the hardware interface therefore switches torque
  off at start (`disable_torque_at_init`). With `hardware:=real` it refuses to start
  instead, which is the safe behaviour on the arm.
- A freshly started drive answers on the factory ID 1; the tool first moves each
  drive to its joint ID (`--assign-ids`), over that drive's own connection.
- The gripper stays on mock hardware (separate project).

Start the six simulated drives from the doppelstep repository
([getting started](https://systemfromscratch.com/sfs-doppelstep/getting-started/)), one per terminal or in the background:

```bash
# in the sfs-doppelstep repository (WSL 2 or Linux, Docker); build once:
docker compose run --rm zephyr west build -b native_sim/native/64 -s app -d build-native
# six drives, each in its own container with its own flash file and bus link:
for i in 0 1 2 3 4 5; do
  docker compose run -d --rm --name dxl$((i+1)) -p $((5555+i)):5555 zephyr \
    python3 tools/sim/run_native.py run --tcp 5555 --link /tmp/ttyDXL -- --flash=/tmp/flash.bin
done
# stop them: docker stop dxl1 dxl2 dxl3 dxl4 dxl5 dxl6
```

`--link` and `--flash` keep the instances apart: by default all of them would use the
same bus link and flash file in the shared build directory, and an ID written to one
drive would land in the flash of the others.

Stop a Robot PC that still runs with mock hardware first: both use the `robot_pc` service and its fixed address. Then start the Robot PC with the SIL override, and check it as usual from a second host:

```bash
docker compose -f docker/docker-compose.yml -f docker/docker-compose.sil.yml up --build robot_pc
docker compose -f docker/docker-compose.yml run --rm probe smx_smoke_test.sh
```

For one-off commands in the image (xacro, `ls`, connection checks) use the `probe` service: `docker compose run robot_pc` fails with *Address already in use* while the Robot PC runs, because of the fixed address.

`SMX_SIL_DEVICES` and `SMX_SIL_IDS` in `docker/.env` change the addresses and IDs,
for example to start with one drive: `SMX_SIL_DEVICES=host.docker.internal:5555` and
`SMX_SIL_IDS=1` (the other joints then have no drive and the hardware interface
reports them missing). On a Linux host without Docker Desktop,
`host.docker.internal` is mapped to the host by `extra_hosts`.

The arm configuration for `sil` and `real` is in
`smartmanipulator_x_description/urdf/smartmanipulator_x.ros2_control.xacro`: IDs 1–6,
extended position mode, ID 3 mirrored, and transmission matrices that map the two
shoulder drives onto `j2_shoulder` and include the 57/11 elbow gearbox. The values
still to confirm in SIL are listed in the
[compatibility specification](../dynamixel/compatibility-spec.md).

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

### Moving to the robot

The image has no host-specific state. On the CM4 (arm64) it is pulled as a multi-architecture image, and `smx_net` is replaced by the real network (Wi-Fi): drop the `networks` entries and use `network_mode: host`. `ROS_DOMAIN_ID` and the Fast DDS profile stay the same. The planned deployment is described in [Robot PC on the CM4-Duino](cm4-duino.md).

## Hardware shell

Build and start an interactive Robot PC shell with a serial device from the repository root:

```bash
docker compose -f docker/docker-compose.yml -f docker/docker-compose.hw.yml run --rm robot_pc bash
```

On a development PC the device is the ST-LINK virtual COM port of a doppelstep board (typically `/dev/ttyACM0`) or a USB-UART adapter; on the robot it is `/dev/ttyDXL`. Set `SMX_SERIAL_DEVICE` in `docker/.env` (template: `docker/env.example`) to the device path and make sure the host user may open it. Docker Desktop on Windows does not pass a COM port into a Linux container; use a Linux host, or `usbipd-win` with WSL 2.

Inside the container, inspect the available packages with:

```bash
ros2 pkg list | grep -E '^(dynamixel_sdk|dynamixel_interfaces|dynamixel_hardware_interface|smartmanipulator_x_)'
```

`robot.launch.py` refuses `hardware:=real` until the real-hardware path is verified in SIL and on the bench (Stages 1 and 2 of the [integration plan](../plan/doppelstep-cm4.md)). No physical bring-up is validated yet.

## Network and operation

The Robot PC communicates with the Operator PC using ROS 2 DDS over the configured network. Configure the same `ROS_DOMAIN_ID` on both computers and validate DDS discovery, selected network interfaces, multicast/unicast policy, and firewall behavior on the actual network. Do not use SSH as the ROS transport.

Do not enable motor motion until the actuator mapping, motor-driver configuration, limits, homing behavior, and an appropriate stop/safety procedure have been reviewed on the assembled robot. Test incrementally: mock hardware, simulated drives (SIL), one drive on the bench, one physical joint, then the complete mechanism.

## Repository ownership

- Robot PC Docker and bringup: `docker/` and `ros2_ws/src/smartmanipulator_x/smartmanipulator_x_bringup/`.
- Project controller and hardware configuration: `ros2_ws/src/smartmanipulator_x/smartmanipulator_x_config/`.
- Canonical robot description location: `ros2_ws/src/smartmanipulator_x/smartmanipulator_x_description/`.
- Upstream dependencies: separate source checkouts selected by `ros2_robot.repos`; pin immutable revisions for reproducible builds before production use.