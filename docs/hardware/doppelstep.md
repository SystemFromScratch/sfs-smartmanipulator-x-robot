# doppelstep joint drives

Each stepper joint of the arm is driven by its own
[**doppelstep**](https://github.com/SystemFromScratch/sfs-doppelstep) drive: a
small stepper controller that answers on the DYNAMIXEL bus as a smart servo.
For the Robot PC every joint motor therefore looks like a DYNAMIXEL
XM430-W350, so the unchanged ROBOTIS `dynamixel_hardware_interface` and
DynamixelSDK are meant to drive it (to be verified, see the
[compatibility specification](../dynamixel/compatibility-spec.md)).

> **Status (2026-11-15):** doppelstep v0.1.0 is verified on a PC with a
> simulated motor (`native_sim`), not yet with a real motor. One
> B-G431B-ESC1 board is ready on the bench. The single-wire bus interface is
> not implemented yet. The [doppelstep documentation](https://systemfromscratch.com/sfs-doppelstep/) is authoritative
> for the drive; this page records only what SmartManipulator-X relies on and
> links to the details.

## Hardware

| Item | Value |
| --- | --- |
| Board | ST **B-G431B-ESC1** discovery kit (power stage and STM32 on one board, with an on-board ST-LINK) |
| MCU | STM32G431CB, Cortex-M4F at 170 MHz, 128 KiB flash, 32 KiB RAM |
| Motor | Two-phase (bipolar) stepper; NEMA 14, 17 and 23 in this arm ([joint motors](wiring.md#joint-motors)) |
| Firmware | Zephyr RTOS, MCUboot (RSA-2048 signed images, serial recovery over the DYNAMIXEL bus); [architecture](https://systemfromscratch.com/sfs-doppelstep/architecture/) |
| Control | Current loop at 20 kHz, motion profiles at 1 kHz, 16 microsteps per full step |
| Protection | Overcurrent, bus voltage (10–28 V) and shared-leg faults switch the outputs off in the current-loop interrupt; NTC overtemperature; coil self-test before torque ([protection](https://systemfromscratch.com/sfs-doppelstep/protection/)) |
| Supply | 10–28 V accepted, tuned for 24 V ([hardware](https://systemfromscratch.com/sfs-doppelstep/hardware/#supply-and-bus-voltage)) |
| Motor connection | Shared-leg topology: coil A between U and W, coil B between V and W ([motor wiring](https://systemfromscratch.com/sfs-doppelstep/hardware/#motor-wiring), [Wiring](wiring.md#joint-drives-b-g431b-esc1)) |

## What the Robot PC sees

| Item | Value |
| --- | --- |
| Protocol | DYNAMIXEL Protocol 2.0 |
| Model | XM430-W350, model number **1020** |
| Control Table | The XM430-W350 table, with the range and access checks of the real servo |
| Operating modes | Position, extended position, velocity |
| Instructions | Including Sync/Bulk Read and Write, Fast Sync/Bulk Read, Reboot, Factory Reset |
| Other | Bus Watchdog; EEPROM area kept in flash |
| Host tools | `dynamixel_hardware_interface`, DynamixelSDK, DYNAMIXEL Wizard |
| Bus UART | USART2 on PB3 (TX) / PB4 (RX); factory 57600 bps, up to 4.5 Mbps ([DYNAMIXEL emulation](https://systemfromscratch.com/sfs-doppelstep/dynamixel/)) |

Because the model number is a real ROBOTIS one, no project-specific model
file is needed on the host. Which registers the Jazzy hardware interface
actually reads and writes is checked in the
[compatibility specification](../dynamixel/compatibility-spec.md).

## Connection

| Situation | Link | Status |
| --- | --- | --- |
| Simulation (SIL) | Firmware as `native_sim` on the PC, serial port over TCP (`tools/sim/run_native.py run --tcp 5555`) | Works; six instances drive the Robot PC over a virtual DYNAMIXEL bus ([SIL](../robot-pc/index.md#sil-simulated-doppelstep-drives), [tutorial](../tutorial-simulation.md)) |
| Bench | PC ↔ ST-LINK **virtual COM port** of the board; SWD and RTT logging stay available at the same time | Planned (decision D6) |
| Arm | Single-wire half-duplex DYNAMIXEL bus from the CM4-Duino to all drives, on pad J3-2 (USART2_TX, PB3) and J3-5 (GND) | Planned, see [DYNAMIXEL bus](../dynamixel/bus.md) and [Wiring](wiring.md#joint-drives-b-g431b-esc1) |

The ST-LINK virtual COM port is a full-duplex UART bridge on the same USART2.
It tests the protocol and timing, not the single-wire physical layer. Because
USART2 carries the bus, the doppelstep console and log run over SEGGER RTT
through the debug probe. The single-wire mode is planned in doppelstep as the
`single-wire;` property on `&usart2` (TX pin only).

## Per-drive configuration

Set on every drive before it joins the bus (EEPROM area, for example with
DYNAMIXEL Wizard or the doppelstep bench GUI):

| Register | Value |
| --- | --- |
| ID | Joint ID from the [joint contract](../robot-pc/index.md#joint-contract) (1–6) |
| Baud Rate | Bus baud rate, see [DYNAMIXEL bus](../dynamixel/bus.md#bus-parameters) |
| Return Delay Time | Default until the bus timing is measured |
| Drive Mode | Reverse direction where the motor turns against the joint convention |
| Run current | Rated current of the joint motor ([joint motors](wiring.md#joint-motors), set in the [motor node configuration](https://systemfromscratch.com/sfs-doppelstep/configuration/)) |

## Bench tools

The doppelstep repository has a [bench GUI](https://systemfromscratch.com/sfs-doppelstep/gui/) (live plots, CSV
recording, the full Control Table, SIL scenarios with an HTML report, firmware
update) and a smoke test (`tools/sim/dxl_smoke_test.py`). Bring up every drive
with the doppelstep [bring-up checklist](https://systemfromscratch.com/sfs-doppelstep/hardware/#bring-up-checklist)
before connecting it to the Robot PC; after driver changes, run its
[hardware checklist](https://systemfromscratch.com/sfs-doppelstep/hardware-checklist/).

## doppelstep documentation

| Page | Use in this project |
| --- | --- |
| [Getting started](https://systemfromscratch.com/sfs-doppelstep/getting-started/) | Build, flash, run `native_sim` |
| [Hardware and bring-up](https://systemfromscratch.com/sfs-doppelstep/hardware/) | Motor wiring, supply, bring-up checklist |
| [Dead time of the power stage](https://systemfromscratch.com/sfs-doppelstep/dead-time/) | Required measurement before the first motor |
| [Protection](https://systemfromscratch.com/sfs-doppelstep/protection/) | Self-test, trips, Hardware Error Status |
| [DYNAMIXEL emulation](https://systemfromscratch.com/sfs-doppelstep/dynamixel/) | Control Table and instructions the Robot PC uses |
| [Configuration](https://systemfromscratch.com/sfs-doppelstep/configuration/) | Motor node values (current, trip limits) |
| [GUI](https://systemfromscratch.com/sfs-doppelstep/gui/) | Bench tool |
| [Architecture](https://systemfromscratch.com/sfs-doppelstep/architecture/) | Firmware structure |
