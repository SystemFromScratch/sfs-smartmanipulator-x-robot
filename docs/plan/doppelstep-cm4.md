# Plan: doppelstep drives on a CM4-Duino Robot PC

> **Status (2026-11-15):** plan agreed, no implementation yet. This page
> defines the target architecture of the project. Update the
> checklists here as the work progresses; the summary is on the
> [project status](../status.md) page.

## Goal

Run the Robot PC software from this repository on a Waveshare **CM4-Duino**
with a Raspberry Pi **CM4 (with Wi-Fi)**. It drives the arm joints through
[sfs-doppelstep](https://github.com/SystemFromScratch/sfs-doppelstep) stepper
drives that present themselves as DYNAMIXEL XM430-W350 servos (Protocol 2.0).
The Operator PC ([sfs-smartmanipulator-x-operator](https://github.com/SystemFromScratch/sfs-smartmanipulator-x-operator))
stays unchanged and connects over ROS 2 DDS.

## Decisions

| # | Decision | Status |
| --- | --- | --- |
| D1 | Joint drives: one **doppelstep** drive (ST B-G431B-ESC1) per stepper motor | Agreed |
| D2 | **One repository.** This repo stays the Robot PC and builds the CM4 artifact (arm64 image + deployment files). No separate controller repo for the software. A separate repo only for a future interface PCB (KiCad) | Agreed |
| D3 | Operator PC ↔ Robot PC link: **Wi-Fi** of the CM4 (the CM4-Duino has no RJ45 and only one USB 2.0 port) | Agreed |
| D4 | Joint bus speaks **plain DYNAMIXEL Protocol 2.0**, with no second link layer: DXL is already a collision-free master/slave protocol, and a second MAC would break direct compatibility with DynamixelSDK, `dynamixel_hardware_interface` and DYNAMIXEL Wizard | Agreed |
| D5 | Half-duplex single-wire UART driver is implemented **in doppelstep** (Zephyr, STM32G431 USART single-wire mode) | Agreed |
| D6 | Bench link PC ↔ B-G431B-ESC1: **ST-LINK VCP** (keeps SWD/RTT debugging available). A separate USB-UART adapter only if needed later | Agreed |
| D7 | Physical layer in the arm: TTL single-wire first; RS-485 (auto-direction transceiver) only if Stage 4 noise measurements require it. No real ROBOTIS servos share the bus, so the choice is free | Proposed |
| D8 | Baud rate **1 Mbps** (OpenMANIPULATOR-X default); doppelstep factory setting 57600, up to 4.5 Mbps | Proposed, verify ST-LINK VCP limit in Stage 2 |
| D9 | Gripper (MG996R, PWM): **virtual DYNAMIXEL on ID 7** (small MCU reusing the doppelstep X430 emulator, PWM output), so the joint contract and `gripper_controller` stay unchanged. Built as a **separate project after** the chain Operator PC → Robot PC → doppelstep works; until then the gripper stays on mock hardware | Agreed |
| D10 | Motor supply **24 V** (doppelstep accepts 10–28 V and is tuned for 24 V; board TVS 26 V stand-off). First runs at 12 V on a laboratory supply with current limit | Proposed |

## Target architecture

```text
 Operator PC (MoveIt 2, RViz2)
        │  ROS 2 DDS over Wi-Fi (ROS_DOMAIN_ID=42)
        ▼
 CM4-Duino + CM4 (Raspberry Pi OS, Docker)
   robot_pc container (arm64): ros2_control
     -> dynamixel_hardware_interface -> DynamixelSDK
     -> /dev/ttyDXL (PL011 UART, GPIO14/15 on the Arduino header, BT disabled)
        │  DYNAMIXEL Protocol 2.0, half-duplex single-wire TTL, 1 Mbps
        ├── doppelstep ID 1  j1_base
        ├── doppelstep ID 2  j2_shoulder (motor A)
        ├── doppelstep ID 3  j2_shoulder (motor B, mirrored)
        ├── doppelstep ID 4  j3_elbow
        ├── doppelstep ID 5  j4_forearm_roll
        └── doppelstep ID 6  j5_wrist
   gripper MG996R: ID 7 virtual DXL (separate project, later)
```

The ID map is the existing [joint contract](../robot-pc/index.md#joint-contract);
only the device behind each ID changes.

## Stage 0: bus decisions and half-duplex driver (doppelstep)

- [ ] Single-wire half-duplex USART driver in doppelstep (`single-wire;` on `&usart2`, PB3, open-drain; turnaround vs. Return Delay Time)
- [ ] Confirm D7 and D8, write them into the [compatibility specification](../dynamixel/compatibility-spec.md)
- [ ] Configure IDs 1–6 and the baud rate on each doppelstep (EEPROM area)
- [ ] Check Secondary (Shadow) ID support in doppelstep for the mirrored J2 pair, otherwise use `transmission_to_joint_matrix`

**Exit:** the doppelstep driver passes its SIL tests in single-wire mode; D7 and D8 recorded.

## Stage 1: SIL on the PC, no hardware

- [ ] Virtual DXL bus: small Python tool that connects N doppelstep `native_sim` instances (`tools/sim/run_native.py run --tcp <port>`) into one shared half-duplex bus and exposes it as a pty (`socat` / pty bridge) at `/dev/ttyDXL`
- [ ] New Compose profile `sil`: `robot_pc` with the real hardware interface on the virtual bus, gripper as mock (or virtual DXL)
- [ ] `dynamixel_hardware_interface` configuration in `smartmanipulator_x_description` (ports, IDs, J2 transmission)
- [ ] Remove the `use_mock_hardware:=false` guard in `robot.launch.py` once SIL passes
- [ ] Extend `smx_smoke_test.sh` for the SIL profile; run it in CI if the sims fit into the runner

**Exit:** the Operator PC plans and executes a trajectory; the doppelstep sims follow it; smoke test green.

## Stage 2: one B-G431B-ESC1 on the bench (PC, ST-LINK VCP)

- [ ] `docker-compose.hw.yml` points at the ST-LINK VCP device (one joint, others mock)
- [ ] Verify the maximum VCP baud rate and USB latency against D8
- [ ] Bring up the drive with the doppelstep [bring-up checklist](https://systemfromscratch.com/sfs-doppelstep/hardware/#bring-up-checklist) (dead time first)
- [ ] Verify Control Table accesses and timing used by `dynamixel_hardware_interface` (Sync/Bulk Read, Fast Sync Read) on real hardware; RTT logging in parallel
- [ ] Note: the VCP is a full-duplex bridge, so this stage tests the protocol and timing, not the single-wire physical layer; test single-wire separately with a USB-UART and a half-duplex wiring

**Exit:** one real joint follows trajectories from the Operator PC; compatibility spec rows set to *Verified*.

## Stage 3: Robot PC on the CM4-Duino

- [ ] Multi-arch image (`docker buildx`, `linux/amd64` + `linux/arm64`) published to GHCR by `docker-publish.yml`
- [ ] `deploy/cm4-duino/`: `config.txt` fragment (`dtoverlay=disable-bt`, UART, USB if needed), udev rule for `/dev/ttyDXL`, systemd unit that starts Compose, provisioning script
- [ ] Compose profile `hw-cm4` and per-target hardware config (`sim`, `sil`, `hw-pc`, `hw-cm4`) so port, baud and IDs are not hard-coded in launch files
- [ ] Bus interface on the Arduino header (3.3 V UART to single-wire bus, motor power distribution); first on a breadboard, later possibly a shield in its own hardware repo
- [ ] Fast DDS profile for Wi-Fi (unicast peers instead of multicast if discovery is unreliable)

**Exit:** the CM4 boots, starts `robot_pc` automatically and drives the bench joint from the Operator PC over Wi-Fi.

## Stage 4: full arm, two hosts

- [ ] All six doppelstep drives on the arm (gripper: separate project, D9)
- [ ] Operator PC on a second computer over Wi-Fi (two-host operation)
- [ ] Measure bus noise next to the stepper drives; decide TTL vs. RS-485 (D7)
- [ ] Measure joint limits and replace the URDF placeholders

**Exit:** full pick-and-place demo; README status checklist complete.

## Documentation

Done on 2026-11-15: the documentation describes the doppelstep / CM4-Duino
architecture, including the [wiring](../hardware/wiring.md). Remaining: the
Operator PC README still describes the old controller. The current state of every item is on the
[project status](../status.md) page.

## Risks

| Risk | Mitigation |
| --- | --- |
| Linux UART timing on the CM4 (turnaround, latency) breaks DXL return timing | Hardware half-duplex / auto-direction interface, never GPIO direction switching from user space; check Return Delay Time |
| DDS discovery over Wi-Fi is unreliable or slow | Unicast Fast DDS profile, fixed IP for the CM4 |
| Stepper drive noise on a TTL bus | Short wiring, common ground star point, RS-485 fallback (D7) |
| ST-LINK VCP limits baud rate or adds latency | Separate USB-UART adapter (D6) |
| Single USB port on the CM4-Duino | Keep the joint bus on the PL011 UART; USB stays free |
