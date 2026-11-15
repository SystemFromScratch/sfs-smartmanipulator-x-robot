# DYNAMIXEL bus

The Robot PC drives the joints over one DYNAMIXEL Protocol 2.0 bus. The CM4
is the bus master; the six [doppelstep drives](../hardware/doppelstep.md)
answer as XM430-W350 servos. The bus carries only standard DYNAMIXEL
packets, so it is built for the ROBOTIS host software, DYNAMIXEL Wizard and a
USB-to-DYNAMIXEL adapter without changes; the
[compatibility specification](compatibility-spec.md) records what is verified.

> **Status (2026-11-15):** planned. Decisions D4–D8 of the
> [integration plan](../plan/doppelstep-cm4.md#decisions); the parameters
> marked *proposed* are confirmed in Stage 0 and Stage 2.

## Topology

```text
 CM4-Duino (bus master)
   GPIO14 TXD0 ─┐
   GPIO15 RXD0 ─┤ bus interface (open-drain send, echo-blocking receive)
                └── DATA ──┬───────────┬───────────┬── … ──┐
                    GND  ──┼───────────┼───────────┼── … ──┤
                           │           │           │       │
                       doppelstep  doppelstep  doppelstep  doppelstep
                         ID 1        ID 2        ID 3   …    ID 6
```

Only one device sends at a time: the master sends an instruction packet and
only the addressed device answers with a status packet (Sync/Bulk Read
answers come one after another in ID order). Protocol 2.0 needs no extra
arbitration, so no second protocol layer is used on this bus (decision D4).

## Bus parameters

| Parameter | Value | Status |
| --- | --- | --- |
| Protocol | DYNAMIXEL Protocol 2.0 | Fixed |
| Physical layer | Single-wire half-duplex, open-drain, 3.3 V, one 470 Ω pull-up at the master; RS-485 with an auto-direction transceiver if Stage 4 noise measurements require it | Proposed (D7) |
| Baud rate | **1 Mbps** (OpenMANIPULATOR-X default); doppelstep ships with 57600 bps and supports up to 4.5 Mbps ([DYNAMIXEL emulation](https://systemfromscratch.com/sfs-doppelstep/dynamixel/)) | Proposed (D8) |
| Master UART | CM4 PL011 UART0 on GPIO14/GPIO15, `/dev/ttyAMA0` with Bluetooth disabled, stable name `/dev/ttyDXL` from a udev rule | Planned |
| Device side | STM32G431 USART2 in single-wire half-duplex mode on PB3 (B-G431B-ESC1 pad J3-2), open-drain; planned in doppelstep as `single-wire;` on `&usart2` ([hardware](https://systemfromscratch.com/sfs-doppelstep/hardware/#dynamixel-bus)) | Not implemented (Stage 0) |

### ID map

| ID | Device | Joint | Controller |
| --- | --- | --- | --- |
| 1 | doppelstep | `j1_base` | `arm_controller` |
| 2 | doppelstep | `j2_shoulder`, motor A | `arm_controller` |
| 3 | doppelstep | `j2_shoulder`, motor B (mirrored) | `arm_controller` |
| 4 | doppelstep | `j3_elbow` | `arm_controller` |
| 5 | doppelstep | `j4_forearm_roll` | `arm_controller` |
| 6 | doppelstep | `j5_wrist` | `arm_controller` |
| 7 | Gripper (virtual DYNAMIXEL, separate project) | `gripper` | `gripper_controller` |

The map is the [joint contract](../robot-pc/index.md#joint-contract) of the
Robot PC. The two shoulder motors are mapped onto one joint with the
`transmission_to_joint_matrix` / `joint_to_transmission_matrix` parameters of
`dynamixel_hardware_interface`; whether doppelstep also supports the
Secondary (Shadow) ID of the XM430 is checked in Stage 0.

## Direction control on the master

The CM4 sends and receives on separate pins; the bus has one data line. The
interface between them must release the line right after the last stop bit,
before the addressed drive answers (Return Delay Time), and it must keep the
CM4 from receiving its own packets, because DynamixelSDK does not discard an
echo. Switching a direction GPIO from Linux user space is too slow and too
jittery for this, so the interface needs no direction signal:

- **Send:** an open-drain buffer (74LVC1G07) pulls DATA low for every 0 bit
  of TXD0; one pull-up resistor at the master pulls DATA high.
- **Receive:** an OR gate passes DATA to RXD0 only while TXD0 is high, so the
  CM4's own 0 bits never reach its receiver.
- **Drives:** the STM32 USART runs in single-wire half-duplex mode with its
  pin open-drain, so all devices only pull the line low.

Circuit, parts and pins: [Wiring](../hardware/wiring.md#robot-pc-cm4-duino-to-the-bus-interface).
It is built on a breadboard first (Stage 3) and may later become a shield for
the CM4-Duino. If the noise measurements of Stage 4 require RS-485, an
auto-direction transceiver replaces the open-drain stage at every node.

## Power and ground

Full wiring: [Wiring](../hardware/wiring.md).

- Motor supply of the drives separate from the 5 V supply of the CM4-Duino.
- One common ground between the CM4-Duino and every drive (bus reference),
  with a star point at the motor supply minus; the motor current must not
  flow through the bus ground.
- Keep the bus cable short and away from the motor phases; measure the noise
  on the assembled arm before deciding between TTL and RS-485.

## Linux configuration (planned)

```ini
# /boot/firmware/config.txt
enable_uart=1
dtoverlay=disable-bt
```

```text
# /etc/udev/rules.d/99-smx-dxl.rules
KERNEL=="ttyAMA0", SYMLINK+="ttyDXL", GROUP="dialout", MODE="0660"
```

Disable the serial console on UART0 (`raspi-config` → Interface Options →
Serial Port: login shell **no**, hardware **yes**). The Robot PC container gets
`/dev/ttyDXL` through the hardware Compose override.

## Simulation

In the SIL setup (Stage 1) a small tool joins several doppelstep `native_sim`
instances into one virtual half-duplex bus and exposes it to the Robot PC as
a pseudo-terminal at `/dev/ttyDXL`, so the real-hardware `ros2_control` path
runs without any board.
