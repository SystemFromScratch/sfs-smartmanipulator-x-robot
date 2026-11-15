#!/bin/bash
# SmartManipulator-X: start the Robot PC in the SIL setup.
#
# 1. smx_dxl_bus.py joins the simulated doppelstep drives (TCP) into one virtual
#    DYNAMIXEL bus at /dev/ttyDXL and gives every drive its joint ID.
# 2. The Robot PC bringup runs with hardware:=sil on that bus.
#
# Used by docker/docker-compose.sil.yml. Settings (environment):
#   SMX_SIL_DEVICES  host:port of the drives, in ID order
#   SMX_SIL_IDS      joint IDs, one per drive (default 1,2,3,4,5,6)
#   SMX_BAUD_RATE    passed to the hardware interface (default 9600). The virtual bus
#                    ignores it, but DynamixelSDK derives its packet timeout from it
#                    for the reads at start (activation, Fast Sync Read fallback).
#   SMX_UPDATE_RATE  controller_manager rate in Hz (default 25). In the control loop
#                    dynamixel_hardware_interface sets the read timeout to one control
#                    period (setPacketTimeout(period_ms)), whatever the baud rate. A
#                    Sync Read of six simulated drives takes up to about 25 ms (10 ms
#                    polling of each drive), so the period must be longer than that:
#                    50 Hz (20 ms) gives a few timeouts per second, 25 Hz (40 ms) none.

set -euo pipefail

DEVICES="${SMX_SIL_DEVICES:-host.docker.internal:5555,host.docker.internal:5556,host.docker.internal:5557,host.docker.internal:5558,host.docker.internal:5559,host.docker.internal:5560}"
IDS="${SMX_SIL_IDS:-1,2,3,4,5,6}"
LINK=/dev/ttyDXL
READY="$(mktemp -u)"

python3 /opt/smx/sim/smx_dxl_bus.py --devices "${DEVICES}" --assign-ids "${IDS}" \
  --link "${LINK}" --ready-file "${READY}" &
BUS_PID=$!
trap 'kill "${BUS_PID}" 2>/dev/null || true' EXIT

echo "[smx_sil] waiting for the virtual bus (drives: ${DEVICES}) ..."
while [ ! -f "${READY}" ]; do
  if ! kill -0 "${BUS_PID}" 2>/dev/null; then
    echo "[smx_sil] the virtual bus did not start; are the doppelstep simulations running?" >&2
    exit 1
  fi
  sleep 0.2
done

ros2 launch smartmanipulator_x_bringup robot.launch.py \
  hardware:=sil port_name:="${LINK}" baud_rate:="${SMX_BAUD_RATE:-9600}" \
  update_rate:="${SMX_UPDATE_RATE:-25}" &
LAUNCH_PID=$!
trap 'kill -INT "${LAUNCH_PID}" 2>/dev/null; wait "${LAUNCH_PID}" 2>/dev/null; kill "${BUS_PID}" 2>/dev/null || true' EXIT INT TERM
wait -n "${LAUNCH_PID}" "${BUS_PID}"
