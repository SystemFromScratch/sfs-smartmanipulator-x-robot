# DYNAMIXEL compatibility specification

**Status: unverified.** This is the shared contract between the Robot PC (ROBOTIS host software) and the [doppelstep](../hardware/doppelstep.md) drives on the [DYNAMIXEL bus](bus.md). doppelstep is designed to behave like an XM430-W350, but no row below is verified against the Jazzy host sources or on hardware yet. Keep unknowns explicit.

## Scope

Each doppelstep drive is a DYNAMIXEL Protocol 2.0 device that controls one stepper motor of the BCN3D Moveo. The Robot PC drives all of them through the stock ROBOTIS `dynamixel_hardware_interface` and DynamixelSDK. The gripper (ID 7) is a separate project and gets its own rows when it starts.

The ROBOTIS OpenMANIPULATOR-X source is a software-stack reference, not evidence that its stock actuator model, joint names, motion ranges, or register usage fit the Moveo build.

## Sources to pin and inspect

For every finding, record the immutable commit or release, file path, and relevant symbol/line or documented section. Branch names such as `jazzy` can move and are not sufficient as reproducible evidence.

- [DynamixelSDK](https://github.com/ROBOTIS-GIT/DynamixelSDK)
- [dynamixel_hardware_interface](https://github.com/ROBOTIS-GIT/dynamixel_hardware_interface)
- [dynamixel_interfaces](https://github.com/ROBOTIS-GIT/dynamixel_interfaces)
- [OpenMANIPULATOR ROS 2](https://github.com/ROBOTIS-GIT/open_manipulator)
- [doppelstep](https://github.com/SystemFromScratch/sfs-doppelstep) firmware release and its Control Table implementation ([DYNAMIXEL emulation](https://systemfromscratch.com/sfs-doppelstep/dynamixel/))
- ROBOTIS XM430-W350 e-Manual (the reference doppelstep follows)

Inspect the host implementation rather than guessing from the Control Table PDF: identify the actual startup reads/writes, register widths and signedness, command/state interfaces, operating modes, packet instructions, status/error handling, retries, timeout behavior, and update loop. Confirm what behavior is meaningful for a stepper-driven Moveo joint.

## Evidence-backed device contract

Replace `Unverified` only when source or hardware evidence is recorded. If a requirement does not apply to the stepper drive, document why and how the host path handles it.

| Requirement | Expected (design) | Verified value | Source revision and evidence |
| --- | --- | --- | --- |
| Host package versions/commits | Jazzy branches of the ROBOTIS packages in `ros2_robot.repos` | Unverified | Unverified |
| Device model and protocol | XM430-W350, model number 1020, Protocol 2.0 | Unverified | Unverified |
| Device IDs and discovery | IDs 1–6 per the [ID map](bus.md#id-map), PING | Unverified | Unverified |
| Physical layer, baud rate, response timing | Single-wire half-duplex, 1 Mbps proposed, Return Delay Time default | Unverified | Unverified |
| Protocol instructions actually used | Read, Write, Sync/Bulk Read and Write, Fast Sync/Bulk Read (to be confirmed in the host source) | Unverified | Unverified |
| Control Table addresses, widths, signedness, access rules | XM430-W350 table | Unverified | Unverified |
| Initialization and configuration sequence | From the hardware-interface source | Unverified | Unverified |
| Command interfaces and operating modes | Position / extended position | Unverified | Unverified |
| State interfaces and measurement source | Position from the drive's step counter (open loop), velocity, current | Unverified | Unverified |
| Torque enable and fault behavior | Hardware Error Status, Torque Enable, Bus Watchdog | Unverified | Unverified |
| Update rate, latency, retries, timeouts | Controller rate 100 Hz (`controllers.yaml`); the read timeout of the host is one control period | SIL only: 25 Hz, no read timeouts; the simulated drives answer a Sync Read of six IDs within about 25 ms. Real bus: Unverified | SIL run 8, 2026-11-15 |
| Moveo joint-to-drive mapping, shoulder pair | [Joint contract](../robot-pc/index.md#joint-contract), transmission matrices | Unverified | Unverified |
| Unmodified stock hardware-interface compatibility | Expected | **Works in SIL** with Sync Read and answers in request order; needs the two doppelstep changes of Stage 0 for a real bus | SIL runs 1–8, 2026-11-15 |
| Host configuration (`smartmanipulator_x.ros2_control.xacro`) | `DynamixelHardware`, `port_name`, `baud_rate`, `dynamixel_model_folder` = `/param/dxl_model`, `error_timeout_ms` 500 (5000 in SIL), 5 joints / 6 transmissions, gpio `type dxl`, Operating Mode 4, Drive Mode 1 on ID 3 | Renders with `hardware:=sil`; `param/dxl_model/xm430_w350.model` exists in the `dynamixel_hardware_interface` share of the image. Runs in SIL: all items written, controllers active | xacro output and `ls` in the Robot PC image; SIL runs 4 and 8, 2026-11-15 |

## Verification record

For each test, record hardware and firmware revisions, host OS/ROS distribution, exact source commits, configuration, command, expected result, and observed result. Distinguish the simulated drive (`native_sim`) from a physical stepper axis.

Minimum staged evidence:

1. SIL: the Robot PC opens the virtual bus and pings every simulated drive (Stage 1).
2. Verify Protocol 2.0 framing and status/error responses against the selected DynamixelSDK transport.
3. Record the read/write transactions of the hardware-interface start-up and update loop and check each against doppelstep.
4. Bench: one B-G431B-ESC1 over the ST-LINK virtual COM port follows trajectories from the Operator PC (Stage 2).
5. Single-wire physical layer: the same tests through the half-duplex interface at the chosen baud rate.
6. One physical joint on the arm with its scaling, limits, reference method and stop behavior (Stage 4).

### SIL run 1 (2026-11-15)

Robot PC image built from this repository (ROBOTIS `jazzy` branches), six doppelstep
`native_sim` drives (firmware 52, model 1020) in Docker, `tools/sim/smx_dxl_bus.py`,
`hardware:=sil`.

| Observed | Result |
| --- | --- |
| Port, baud change on the pseudo-terminal | OK |
| PING of IDs 1–6, model 1020 → `xm430_w350.model` | OK |
| Torque state read, `Operating Mode` 4, `Return Delay Time` 0, `Drive Mode` 0 / 1 (ID 3) written | OK |
| Read path: **Fast Sync Read** through indirect addresses (address 634, 10 bytes: Present Position, Velocity, Current) | Set up OK; first readings wrong (j2 206080 rad, j4 3.3·10⁶ rad) |
| Write path: Sync Write through indirect addresses (address 224, 4 bytes: Goal Position) | Set up OK |
| `Torque Enable` write at activation | **Crash**: `stack smashing detected` in DynamixelSDK `Protocol2PacketHandler::writeTxRx` |
| `error_timeout_sec` | Not a parameter of the interface; the name is `error_timeout_ms` (default 500 ms) |

Cause: the first version of the virtual bus did not pass a drive's bytes to the other
drives. Fast Sync Read needs that (the drives append their parts to one common status
packet in turn), so the host received a malformed answer; a stray long status packet
then reached `writeTxRx`, which reads the status into an 11-byte buffer on the stack.
Fixed in the bus (drive-to-drive forwarding, test `test_other_drives_hear_the_answer`)
and in the xacro (`error_timeout_ms`). Note for the real bus: a malformed or late long
status packet can crash the host process in DynamixelSDK; bus noise must not produce
one silently.

### SIL run 2 (2026-11-15)

Same setup with drive-to-drive forwarding in the bus. Same result: wrong positions
(j2 −718751 rad, j4 2.2·10⁶ rad), then the crash at `Torque Enable`.

Cause, from the source of `dynamixel_hardware_interface` (`5613760`, 2026-11-02) and
the doppelstep documentation:

- The interface always tries **Fast Sync Read** first (`use_fast_read_protocol_` is
  hard-coded `true`, no hardware parameter). It falls back to normal Sync Read only if
  the first 10 Fast Sync Read attempts fail; after one success it keeps Fast Sync Read
  for good.
- doppelstep answers Fast Sync/Bulk Read only for its own ID
  ([DYNAMIXEL emulation](https://systemfromscratch.com/sfs-doppelstep/dynamixel/)): with six drives the host gets six packets
  instead of one chained packet, accepts the first as a success and decodes the rest
  as garbage.

**This also applies to the real bus** with six doppelstep drives. Options: (a) doppelstep
chains Fast Sync/Bulk Read answers like the X series (listens to the drive before it),
or (b) doppelstep stays silent on a Fast Sync/Bulk Read that lists other IDs too, so
the host falls back to Sync Read. Tracked in Stage 0 of the
[integration plan](../plan/doppelstep-cm4.md#stage-0-bus-decisions-and-half-duplex-driver-doppelstep).

SIL workaround: the virtual bus drops Fast Sync/Bulk Read (`--fast-read drop`, the
default), which is the behaviour of option (b).

### SIL run 3 (2026-11-15)

With Fast Sync Read dropped by the bus, the interface fell back to Sync Read as
designed, but every Sync Read of IDs 1–6 ended in `COMM_RX_TIMEOUT` (−3001) and the
activation stopped after 500 ms (`Dynamixel Start Fail … SYNC_READ_FAIL`). No crash.

Measured with `tools/sim/smx_bus_timing.py` on the virtual bus: PING 3–17 ms per drive
(the 10 ms polling of the doppelstep pseudo-terminal); a Sync Read of six IDs gets all
six answers within 13–21 ms, below the DynamixelSDK timeout (35 ms at 1 Mbps), but
**in random order**, for example ID 2, 1, 5, 3, 4, 6. DynamixelSDK reads the answers in
the order of the request and drops an answer with another ID, so the later IDs time out.

**This also applies to the real bus**: each doppelstep answers a Sync Read (and Bulk
Read) at once instead of waiting for its turn, so on one wire the answers of six drives
would collide. The X series answers in the order of the request (a device sends after
the status packet of the ID before it). Tracked in Stage 0 of the
[integration plan](../plan/doppelstep-cm4.md#stage-0-bus-decisions-and-half-duplex-driver-doppelstep).

SIL workaround: the virtual bus passes Sync/Bulk Read answers to the host in request
order (`--read-order request`, the default), which is the behaviour of a real bus.

### SIL run 4 (2026-11-15): pass

Virtual bus with Fast Sync Read dropped and Sync Read answers in request order.
Fast Sync Read fails 10 times, the interface switches to Sync Read, reads plausible
positions, enables torque on IDs 1–6 and activates; `joint_state_broadcaster`,
`arm_controller` and `gripper_controller` become active. `smx_smoke_test.sh` from a
second container: **PASS** (trajectory executed by the six simulated doppelstep drives).

Timing in SIL run 4: each Sync Read took 10–20 ms (10 ms polling of the simulated
drives), so the 100 Hz controller loop overran in most cycles, and about 2–3 Sync Reads
per second timed out. SIL was then changed to 50 Hz and `baud_rate` 9600 (run 7); run 8
found the real cause of the timeouts and moved SIL to 25 Hz.
Simulation-only: on a real bus an answer takes well under 1 ms.

### SIL run 7 (2026-11-15)

50 Hz, `baud_rate` 9600, error timeout 5 s, reorder timeout of the bus 100 ms. Start and
fallback to Sync Read as in run 4. In about 35 s: 82 `SyncRead Rx Fail` (about 2.3 per
second, each recovered in the next cycle) and 31 overruns. A normal Sync Read takes
about 20–21 ms, the whole 50 Hz cycle, and a failed cycle ends after about 21 ms as
well: the host gives up after about 20 ms whatever the baud rate, so the expected
longer DynamixelSDK packet timeout at 9600 is not in effect. Open: the bus now logs each
incomplete read (missing ID, delay of every answer) and a latency summary every 10 s;
the next run is to show whether one drive is late or the timeout of the host is fixed.

### SIL run 8 (2026-11-15): pass, no read timeouts

Same setup as run 7. The bus diagnostics answered the open question: **no read was
incomplete** (all six answers arrived every time; last answer after p50 12.7 / p95 21 /
max 25.6 ms), yet the host reported 96 `SyncRead Rx Fail` (−3001, `COMM_RX_TIMEOUT`)
and 24 overruns in about 30 s. Cause: in the control loop
`dynamixel_hardware_interface` sets the packet timeout to the control period,
`port_handler->setPacketTimeout(period_ms)` in `Dynamixel::ProcessReadCommunication`,
which replaces the timeout DynamixelSDK derives from the baud rate. At 50 Hz the host
gives up after 20 ms, and every Sync Read whose last answer comes later fails. This is
why changing the baud rate had no effect.

Fix: SIL runs the controllers at **25 Hz** (`SMX_UPDATE_RATE`, period 40 ms). Result:
`smx_smoke_test.sh` **PASS**, 0 `SyncRead Rx Fail` and 0 overruns after start; the only
read errors are the ten expected Fast Sync Read attempts before the fallback.

**For the real bus:** the read timeout of the host is one control period (10 ms at
100 Hz), not the DynamixelSDK timeout. A Sync Read of all drives, including their
return delay times, must therefore finish well within one period.

How to repeat the check: [SIL tutorial](../robot-pc/sil-tutorial.md).

Do not claim full XM430 emulation or production readiness based only on successful packet exchange. Register behavior, mechanical mapping, and physical motion all require separate evidence.
