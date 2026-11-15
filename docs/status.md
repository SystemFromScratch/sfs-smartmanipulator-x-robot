# Project status

The single place that says what works today. Every other page links here
instead of repeating it. Update this page whenever an item changes.

**As of 2026-11-15.** Legend: **Done** — implemented and checked;
**In progress** — started; **Planned** — agreed, not started;
**Open** — decision or measurement still missing.

## Chain Operator PC → Robot PC → doppelstep

This is the current goal: one command from MoveIt reaches a real doppelstep
drive. The gripper follows afterwards as a separate project.

| Link | State | Evidence or next step |
| --- | --- | --- |
| Operator PC → Robot PC (DDS) in Docker on one computer | **Done** | Operator PC container on `smx_net`; commands arrive and the mock-hardware simulation follows them |
| Operator PC → Robot PC over Wi-Fi, two computers | Planned | Stage 4 |
| Robot PC → doppelstep in simulation (SIL) | **Done** (2026-11-15) | Six `native_sim` drives, smoke test PASS ([SIL](robot-pc/index.md#sil-simulated-doppelstep-drives)); MoveIt from the Operator PC still to try |
| Robot PC → one doppelstep on the bench (ST-LINK VCP) | Planned | Stage 2; the B-G431B-ESC1 is ready |
| Robot PC on the CM4-Duino → DYNAMIXEL bus | Planned | Stage 3 |
| Full arm (six drives) | Planned | Stage 4 |

## Components

| Component | State | Details |
| --- | --- | --- |
| Robot PC image (ROS 2 Jazzy, DynamixelSDK, `dynamixel_hardware_interface`) | **Done** (amd64) | arm64 build planned for the CM4 |
| Simulation with mock hardware, smoke test over DDS | **Done** | [Getting started](getting-started.md) |
| Robot description from the BCN3D Moveo CAD | **Done** | Joint limits are placeholders |
| Real-hardware `ros2_control` path | **In progress** | `hardware:=sil` uses it on the virtual bus; `hardware:=real` refused until Stage 2 |
| `dynamixel_hardware_interface` configuration (ports, IDs, shoulder transmission) | **Done**, verified in SIL | Gear and pulley ratios still placeholders until measured |
| doppelstep multi-drive bus behaviour (Fast Sync Read, Sync Read turn-taking) | Open | Found in SIL; needed before the real bus ([compatibility specification](dynamixel/compatibility-spec.md#sil-run-3-2026-11-15)) |
| Per-target hardware configuration (`sim`, `sil`, `hw-pc`, `hw-cm4`) | Planned | [Robot PC on the CM4-Duino](robot-pc/cm4-duino.md#hardware-configuration-per-target) |
| Deployment files `deploy/cm4-duino/` | Planned | Stage 3 |
| CM4-Duino documentation and vendor archive | **Done** | [CM4-Duino](hardware/cm4-duino/index.md) |
| CM4-Duino bring-up (OS, UART, Wi-Fi) | Planned | Stage 3 |
| Wiring of the drives, the bus and the supplies | **Done** (documented, not built) | [Wiring](hardware/wiring.md); motor wiring and supply follow the doppelstep hardware documentation |
| Bus interface CM4 ↔ single-wire bus | Planned | Circuit proposed in [Wiring](hardware/wiring.md#robot-pc-cm4-duino-to-the-bus-interface); build and measure in Stage 3 |
| doppelstep firmware | **Done** in simulation (v0.1.0) | Not yet verified with a real motor; [doppelstep documentation](https://systemfromscratch.com/sfs-doppelstep/) |
| doppelstep single-wire half-duplex driver | Planned | Stage 0, in the doppelstep repository |
| Control Table and timing verified against the Jazzy host sources | Open | [Compatibility specification](dynamixel/compatibility-spec.md) |
| Gripper (MG996R) | Open | Separate project after the chain above works; virtual DYNAMIXEL on ID 7; [wiring and requirements](hardware/gripper-servo.md) documented |
| Motor supply voltage | Proposed | 24 V (D10), to be confirmed |
| Joint limits, motor directions, gear ratios on the real arm | Open | Stage 4 |
| Emergency stop and safe power-up | Open | Needed before the full arm moves |

## Decisions

The decisions and their status are kept in the
[integration plan](plan/doppelstep-cm4.md#decisions).
