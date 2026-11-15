# Tutorial: checking SIL step by step

This tutorial walks you through a complete **SIL** check (software in the loop) of the
Robot PC: the real ROS 2 control path (`ros2_control`, the ROBOTIS
`dynamixel_hardware_interface`, DynamixelSDK) talks to six **simulated doppelstep
drives** instead of motors. You need no electronics, only a PC.

> **Status (2026-11-15):** SIL works end to end and `smx_smoke_test.sh` passes. Since
> SIL run 8 the controllers run at 25 Hz in SIL, and after the start there are no
> failed reads and no overruns (see [known limitations](#known-limitations)). New to all
> this? Start with the [beginner tutorial](../tutorial-simulation.md). Stage 1 of the
> [integration plan](../plan/doppelstep-cm4.md#stage-1-sil-on-the-pc-no-hardware).

**What you will have at the end:** six virtual drives on IDs 1–6, the Robot PC with all
controllers active, a test trajectory that completes, and a log that you can read and
judge yourself.

**Time:** about 30 minutes the first time (mostly builds), 2 minutes later.

```text
 Terminal 1-6 (doppelstep)        Terminal 7 (Robot PC)                Terminal 8 (checks)
 drive ID 1 .. ID 6               robot_pc container                   probe container
 native_sim, TCP 5555..5560  <──  smx_dxl_bus.py ── /dev/ttyDXL  <──  ros2_control   <── smx_smoke_test.sh
```

How the parts fit together is described in [Robot PC → SIL](index.md#sil-simulated-doppelstep-drives).

---

## Step 0: Check the prerequisites

| What | Why | Check |
|---|---|---|
| Linux, or Windows with **WSL 2** (e.g. Ubuntu) | doppelstep `native_sim` and the pty bus need Linux | `wsl -l -v` in PowerShell shows `VERSION 2` |
| **Docker Desktop** with WSL integration enabled for your distribution (or Docker Engine on Linux) | both repositories build and run in containers | `docker version` **inside WSL** shows a client and a server |
| `git` and `python3` in WSL | clone the repositories, run the bus tests | `git --version`, `python3 --version` (3.10 or newer) |
| about 10 GB of free disk space | ROS 2 and Zephyr images | |

!!! tip "\"The command 'docker' could not be found in this WSL 2 distro\""
    In Docker Desktop open *Settings → Resources → WSL integration*, enable your
    distribution, press *Apply & restart*, then open a new WSL terminal.

!!! tip "`wsl` opens `docker-desktop` instead of Ubuntu"
    Docker Desktop installs its own distribution `docker-desktop`, which has no `bash`.
    If `wsl -l -v` marks it with `*` (default), open your distribution by name,
    for example `wsl -d Ubuntu-24.04`, or make it the default once with
    `wsl --set-default Ubuntu-24.04`.

!!! note "Python on WSL"
    If `python3` is missing: `sudo apt update && sudo apt install -y python3`.
    The SIL tools use only the Python standard library; nothing has to be installed
    with `pip`.

All commands below run **in WSL terminals** (or in a Linux shell), not in PowerShell.

## Step 1: Get both repositories

```bash
cd ~
git clone https://github.com/SystemFromScratch/sfs-doppelstep.git doppelstep
git clone https://github.com/SystemFromScratch/sfs-smartmanipulator-x-robot.git
```

You can also use an existing clone on the Windows drive, for example
`/mnt/c/.../SmartManipulator-X-Robot-PC`. In this tutorial `ROBOT` stands for the
Robot PC repository and `DOPPEL` for the doppelstep repository. Set them once in every
new terminal:

```bash
export ROBOT=~/sfs-smartmanipulator-x-robot
export DOPPEL=~/doppelstep
```

## Step 2: Test the virtual bus (1 minute)

The tool `tools/sim/smx_dxl_bus.py` joins the drives into one bus. Its tests use fake
drives, so they show whether the bus itself works on your PC:

```bash
cd "$ROBOT/tools/sim"
python3 -m unittest discover -s tests -v
```

**Expected:** `OK` at the end (14 tests at the time of writing). On Windows outside
WSL the pty tests are reported as *skipped*; that is why this tutorial uses WSL.

## Step 3: Build the simulated doppelstep drive

The first time, build the toolchain image and fetch Zephyr into its Docker volume:

```bash
cd "$DOPPEL"
docker compose build
docker compose run --rm zephyr bash scripts/west-init.sh
```

Then build the drive (again after every change to the firmware):

```bash
cd "$DOPPEL"
docker compose run --rm zephyr west build -b native_sim/native/64 -s app -d build-native
```

The first time takes several minutes. **Expected:** the
build ends with a `zephyr.exe` in `build-native/zephyr/`. Details are in the
[doppelstep getting started guide](https://systemfromscratch.com/sfs-doppelstep/getting-started/).

## Step 4: Test one drive on its own

Start one drive and talk to it with the doppelstep smoke test before you start six:

```bash
cd "$DOPPEL"
docker compose run -d --rm --name dxl1 -p 5555:5555 zephyr \
  python3 tools/sim/run_native.py run --tcp 5555 --link /tmp/ttyDXL -- --flash=/tmp/flash.bin
sleep 3
python3 tools/sim/dxl_smoke_test.py --tcp localhost:5555
```

**Expected:** the smoke test reports success; the drive answers PING with model
number 1020, the XM430-W350 it emulates. Leave `dxl1` running.

## Step 5: Start all six drives

```bash
cd "$DOPPEL"
for i in 1 2 3 4 5; do
  docker compose run -d --rm --name dxl$((i+1)) -p $((5555+i)):5555 zephyr \
    python3 tools/sim/run_native.py run --tcp 5555 --link /tmp/ttyDXL -- --flash=/tmp/flash.bin
done
docker ps --filter name=dxl --format '{{.Names}}  {{.Ports}}'
```

**Expected:** six containers `dxl1` … `dxl6` on ports 5555 … 5560.

Every drive starts on the factory ID 1. You do not change that yourself: the bus moves
each drive to its joint ID when the Robot PC starts. Each instance has its own flash
file (`--flash`) and bus link (`--link`), so an ID written to one drive does not land in
the others.

## Step 6: Start the Robot PC in SIL mode

If a Robot PC with mock hardware is still running, stop it first (both use the same
service and fixed address):

```bash
cd "$ROBOT"
docker compose -f docker/docker-compose.yml down
```

Start the Robot PC with the SIL override, in its own terminal; it stays in the
foreground and shows the log:

```bash
cd "$ROBOT"
docker compose -f docker/docker-compose.yml -f docker/docker-compose.sil.yml up --build robot_pc
```

## Step 7: Read the start log

Wait for `Configured and activated gripper_controller`. On the way you should see these
lines, in this order. Tick them off:

- [ ] `[smx_dxl_bus] INFO connected to host.docker.internal:5555` … `:5560`: the bus
      reaches all six drives.
- [ ] `ID 1 present (model 1020)` … `ID 6 present (model 1020)`: each drive is on its
      joint ID.
- [ ] `bus up: /dev/ttyDXL -> /dev/pts/…, 6 drive(s)`: the serial device for the host
      exists.
- [ ] `port_name /dev/ttyDXL / baudrate 9600`: the hardware interface uses the SIL
      settings.
- [ ] `Ping succeeded. Dynamixel model number : 1020` for IDs 1–6.
- [ ] `item_name: Drive Mode data: 1` for **ID 3** only (the mirrored shoulder drive).
- [ ] Ten lines `FastSyncRead TxRx failed (attempt n/10)`, then
      `switching to normal SyncRead permanently`. **This is expected**: the bus drops
      Fast Sync Read, because doppelstep does not yet answer it on a shared bus, and
      the interface falls back to normal Sync Read.
- [ ] `Torque ON` for IDs 1–6, then `Dynamixel Hardware Start!`.
- [ ] `Configured and activated joint_state_broadcaster`, `arm_controller` and
      `gripper_controller`.

`Could not enable FIFO RT scheduling policy` is a harmless warning: the container runs
without real-time privileges.

## Step 8: Run the smoke test

In a second terminal:

```bash
cd "$ROBOT"
docker compose -f docker/docker-compose.yml run --rm probe smx_smoke_test.sh
```

The test runs in the `probe` container, a second ROS 2 host on the same Docker network,
the way the Operator PC will connect later. It checks four things:

1. `/joint_states` arrives from the Robot PC.
2. `joint_state_broadcaster`, `arm_controller` and `gripper_controller` are active.
3. A test trajectory (out and back, 4 s) on `arm_controller` ends with `SUCCEEDED`.
4. The joint positions after the trajectory.

**Expected:** `PASS` on the last line. The trajectory went through DynamixelSDK, the
virtual bus and the doppelstep firmware of six drives, and the positions came back the
same way.

## Step 9: Try it yourself

All commands run in the `probe` container. Open a shell there:

```bash
docker compose -f docker/docker-compose.yml run --rm probe bash
```

Look at the joint states (values in radians):

```bash
ros2 topic echo --once /joint_states
```

Move one joint, for example the base (`j1_base`) by 0.5 rad in 3 s and back:

```bash
ros2 action send_goal /arm_controller/follow_joint_trajectory \
  control_msgs/action/FollowJointTrajectory \
  "{trajectory: {joint_names: [j1_base, j2_shoulder, j3_elbow, j4_forearm_roll, j5_wrist],
    points: [{positions: [0.5, 0, 0, 0, 0], time_from_start: {sec: 3}},
             {positions: [0, 0, 0, 0, 0],   time_from_start: {sec: 6}}]}}"
```

Check the controllers and the hardware:

```bash
ros2 control list_controllers
ros2 control list_hardware_components
```

`j2_shoulder` drives **two** drives (IDs 2 and 3) and `j3_elbow` includes the 57/11
gearbox: the transmission matrices printed at start (`transmission_to_joint_matrix_`)
show this mapping.

## Step 10: Save and judge the log

After about 30 s of running, save the log of the Robot PC:

```bash
cd "$ROBOT"
docker compose -f docker/docker-compose.yml -f docker/docker-compose.sil.yml logs --no-color robot_pc > sil_run.log 2>&1
```

Count the messages that matter:

```bash
grep -c "FastSyncRead TxRx failed" sil_run.log   # expected: 10 (the fallback at start)
grep -c "\] SyncRead Rx Fail" sil_run.log         # failed normal Sync Reads, expected: 0
grep -c "Overrun detected" sil_run.log            # control cycles longer than 40 ms, expected: 0
grep "read incomplete" sil_run.log | head         # which drive did not answer in time
grep "\[smx_dxl_bus\] INFO reads:" sil_run.log    # bus summary every 10 s
```

How to read them:

| Message | Meaning | Acceptable now? |
|---|---|---|
| `FastSyncRead TxRx failed`, 10 times | fallback to Sync Read at start | yes, expected |
| `SyncRead Rx Fail` / `Dynamixel Read Fail (Duration: … ms/5000ms)` | a read timed out (after one control period); the interface keeps the last values and retries in the next cycle | should not appear at 25 Hz; if it does, check that `SMX_UPDATE_RATE` is not set higher in `docker/.env`. The run fails only if the duration reaches 5000 ms |
| `Overrun detected … 25 Hz` | one cycle took more than 40 ms | single ones at start are harmless; regular ones are not expected |
| `read incomplete: missing ID n after x ms` | the bus line for the same event: which ID was missing, and after how long the host gave up | for diagnosis |
| `reads: … last answer after p50 / p95 / max` | how long the drives take to answer | for diagnosis |

The log stays in your repository folder; it is not committed (delete it when you are
done, or attach it to an issue).

## Step 11: Stop everything

```bash
cd "$ROBOT"
docker compose -f docker/docker-compose.yml -f docker/docker-compose.sil.yml down
docker stop dxl1 dxl2 dxl3 dxl4 dxl5 dxl6
```

The drives can also keep running between Robot PC starts: a new Robot PC finds them
again, and in SIL it switches off torque that an earlier run left on.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `waiting for the virtual bus …` and nothing more | the drives are not running or not reachable on 5555–5560 | step 5; `docker ps --filter name=dxl` |
| `cannot reach host.docker.internal:555x` | one drive is missing | start the missing `dxlN` (step 5) |
| `no drive answers on ID n or on the factory ID 1` | a drive has another ID stored in its flash | `docker stop dxlN`, start it again (step 5); the flash file in the container is fresh |
| `Address already in use` | the Robot PC already runs, and `run robot_pc` tries to use the same fixed address | use the `probe` service for one-off commands (step 9) |
| `Torque is enabled, cannot proceed` | only with `hardware:=real`: a drive kept torque from an earlier run | in SIL this does not happen; on the arm switch the drive off and on |
| activation fails with a timeout during the ten Fast Sync Read attempts | error timeout too short | in SIL `error_timeout_ms` is 5000; check that you started with `docker-compose.sil.yml` |
| the smoke test fails at `[1/4]` | the Robot PC is not up yet, or different `ROS_DOMAIN_ID` | wait for `gripper_controller`; use the same `docker/.env` for both |
| `docker` not found in WSL | WSL integration of Docker Desktop is off | step 0 |
| `The container name "/dxl1" is already in use` | the drives still run from an earlier session | keep them (a new Robot PC finds them again) or `docker stop dxl1 … dxl6` and start them again |
| `SyncRead Rx Fail` several times per second | the control period is shorter than a Sync Read of the simulated drives | keep `SMX_UPDATE_RATE` at 25 or lower (step 10) |

## Known limitations

- **Timing of the simulated drives.** A `native_sim` drive polls its serial port every
  10 ms, so a Sync Read of six drives takes up to about 25 ms instead of well under 1 ms
  on the real bus. In the control loop the hardware interface waits for the answers for
  one control period only, whatever the baud rate, so SIL runs the controllers at
  **25 Hz** (40 ms). At 50 Hz (20 ms) about 3 Sync Reads per second time out
  ([SIL run 8](../dynamixel/compatibility-spec.md#sil-run-8-2026-11-15-pass-no-read-timeouts)).
  You can try another rate with `SMX_UPDATE_RATE` in `docker/.env`.
- **Fast Sync Read is not used.** doppelstep answers Fast Sync/Bulk Read only for its
  own ID; on a shared bus that has to be fixed in the firmware (Stage 0 of the
  [integration plan](../plan/doppelstep-cm4.md)). Until then the bus drops it and the
  interface uses normal Sync Read.
- **The gripper** stays on mock hardware; it is a separate project (virtual DYNAMIXEL
  on ID 7).
- SIL checks the protocol and the control path, **not the mechanics**: there is no
  real motor, load or friction behind a simulated drive.

## What next

- Plan with **MoveIt 2 from the Operator PC** against the SIL Robot PC: the
  [beginner tutorial](../tutorial-simulation.md) starts all three parts and moves the
  arm from RViz2.
- Results and open questions of all SIL runs: [DYNAMIXEL compatibility
  specification](../dynamixel/compatibility-spec.md).
- The same check on one real drive (B-G431B-ESC1 on ST-LINK VCP) is Stage 2 of the
  [integration plan](../plan/doppelstep-cm4.md).
