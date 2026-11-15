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
| Update rate, latency, retries, timeouts | Controller rate 100 Hz (`controllers.yaml`) | Unverified | Unverified |
| Moveo joint-to-drive mapping, shoulder pair | [Joint contract](../robot-pc/index.md#joint-contract), transmission matrices | Unverified | Unverified |
| Unmodified stock hardware-interface compatibility | Expected | Unverified | Unverified |

## Verification record

For each test, record hardware and firmware revisions, host OS/ROS distribution, exact source commits, configuration, command, expected result, and observed result. Distinguish the simulated drive (`native_sim`) from a physical stepper axis.

Minimum staged evidence:

1. SIL: the Robot PC opens the virtual bus and pings every simulated drive (Stage 1).
2. Verify Protocol 2.0 framing and status/error responses against the selected DynamixelSDK transport.
3. Record the read/write transactions of the hardware-interface start-up and update loop and check each against doppelstep.
4. Bench: one B-G431B-ESC1 over the ST-LINK virtual COM port follows trajectories from the Operator PC (Stage 2).
5. Single-wire physical layer: the same tests through the half-duplex interface at the chosen baud rate.
6. One physical joint on the arm with its scaling, limits, reference method and stop behavior (Stage 4).

Do not claim full XM430 emulation or production readiness based only on successful packet exchange. Register behavior, mechanical mapping, and physical motion all require separate evidence.
