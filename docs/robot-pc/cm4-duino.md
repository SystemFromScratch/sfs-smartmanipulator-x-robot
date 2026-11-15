# Robot PC on the CM4-Duino

On the robot, the Robot PC will be a Raspberry Pi Compute Module 4 on a
[CM4-Duino](../hardware/cm4-duino/index.md) carrier board. It will run the
same Robot PC image as the development PC, built for arm64, and reach the
Operator PC over Wi-Fi.

> **Status (2026-11-15):** planned (Stage 3 of the
> [integration plan](../plan/doppelstep-cm4.md#stage-3-robot-pc-on-the-cm4-duino)).
> Nothing on this page is implemented yet; it is the target the work is
> measured against.

## What runs where

```text
 CM4-Duino + CM4 (Wi-Fi, eMMC)
 ├── Raspberry Pi OS Bookworm (64-bit) + Docker Engine + Compose v2
 ├── systemd unit smx-robot.service  -> docker compose up robot_pc
 └── robot_pc container (ghcr.io/systemfromscratch/sfs-smartmanipulator-x-robot, arm64)
       ros2_control -> dynamixel_hardware_interface -> DynamixelSDK -> /dev/ttyDXL
                                                                     -> DYNAMIXEL bus -> doppelstep × 6
```

ROS 2 lives only in the container, so the host OS can stay Raspberry Pi OS
(best hardware support for the CM4 and the board) even though ROS 2 Jazzy
targets Ubuntu 24.04.

## Build artifact

| Artifact | Produced by | Status |
| --- | --- | --- |
| Robot PC image for `linux/amd64` and `linux/arm64` | `docker-publish.yml` with `docker buildx`, published to GHCR | Planned (today: amd64 only) |
| `deploy/cm4-duino/` | This repository | Planned |
| SD/eMMC image with everything preinstalled | – | Not planned now; only if provisioning by script becomes too slow |

Planned content of `deploy/cm4-duino/`:

| File | Role |
| --- | --- |
| `config.txt.fragment` | `enable_uart=1`, `dtoverlay=disable-bt`, USB if needed |
| `99-smx-dxl.rules` | udev rule: `/dev/ttyAMA0` → `/dev/ttyDXL` |
| `smx-robot.service` | systemd unit that starts the Robot PC with Compose after Docker and the network are up |
| `docker-compose.cm4.yml` | Compose override: host networking, `/dev/ttyDXL`, image from GHCR instead of a local build |
| `provision.sh` | Installs Docker, copies the files above, disables the serial console, enables the service |

## Hardware configuration per target

Port, baud rate and IDs must not be hard-coded in the launch files. Each
target gets its own hardware configuration, selected by a launch argument or
a Compose profile:

| Target | Hardware | Bus |
| --- | --- | --- |
| `sim` | `mock_components/GenericSystem` | – |
| `sil` | `dynamixel_hardware_interface` | Virtual bus of doppelstep `native_sim` instances |
| `hw-pc` | `dynamixel_hardware_interface` | ST-LINK virtual COM port or USB-UART on a development PC |
| `hw-cm4` | `dynamixel_hardware_interface` | `/dev/ttyDXL` on the CM4-Duino |

## Network

| Item | Plan |
| --- | --- |
| Link to the Operator PC | CM4 Wi-Fi (the CM4-Duino has no Ethernet connector) |
| Address | Fixed IP or DHCP reservation for the CM4 |
| Container network | `network_mode: host` (no `smx_net` on the robot) |
| DDS | Same `ROS_DOMAIN_ID` (42) and Fast DDS UDPv4 profile; switch to a unicast peer list if multicast discovery over Wi-Fi is unreliable |
| Administration | SSH; never the ROS data path |

## Bring-up checklist (planned)

1. Flash Raspberry Pi OS to the eMMC ([CM4-Duino](../hardware/cm4-duino/index.md#flashing-the-emmc)), set host name, user, Wi-Fi and SSH.
2. Run `deploy/cm4-duino/provision.sh`, reboot.
3. Check `/dev/ttyDXL` exists and the serial console is off.
4. Connect one doppelstep drive through the bus interface; ping it with DynamixelSDK or DYNAMIXEL Wizard.
5. Start `smx-robot.service`; run the smoke test from the Operator PC.
