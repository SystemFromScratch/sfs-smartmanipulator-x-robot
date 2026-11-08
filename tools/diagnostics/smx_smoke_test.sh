#!/bin/bash
# SmartManipulator-X: end-to-end check of a running Robot PC over ROS 2 DDS.
#
# Run it on another host of the same network, e.g. the probe container:
#   docker compose -f docker/docker-compose.yml run --rm probe smx_smoke_test.sh
#
# Passes when the Robot PC is discovered, its controllers are active and
# arm_controller executes a short trajectory. Moves the arm: with mock
# hardware this is harmless; never point it at real hardware unattended.

set -uo pipefail

TIMEOUT="${SMX_TIMEOUT:-30}"
ARM_JOINTS="[j1_base, j2_shoulder, j3_elbow, j4_forearm_roll, j5_wrist]"
fail() { echo "FAIL: $*" >&2; exit 1; }

echo "== SmartManipulator-X smoke test (ROS_DOMAIN_ID=${ROS_DOMAIN_ID:-0}, host $(hostname))"

echo "[1/4] Waiting up to ${TIMEOUT}s for /joint_states from the Robot PC ..."
timeout "${TIMEOUT}" ros2 topic echo --once /joint_states sensor_msgs/msg/JointState >/dev/null \
  || fail "no /joint_states: check ROS_DOMAIN_ID, smx_net and that robot_pc is running"
echo "      OK"

echo "[2/4] Controllers on /controller_manager:"
controllers="$(timeout "${TIMEOUT}" ros2 control list_controllers -c /controller_manager 2>&1)" \
  || fail "controller_manager not reachable: ${controllers}"
controllers="$(printf '%s\n' "${controllers}" | sed 's/\x1b\[[0-9;]*m//g')"  # strip colours
echo "${controllers}" | sed 's/^/      /'
for c in joint_state_broadcaster arm_controller gripper_controller; do
  echo "${controllers}" | grep -E "^${c}\b.*\bactive\b" >/dev/null || fail "${c} is not active"
done

echo "[3/4] Sending a test trajectory to arm_controller ..."
goal="{trajectory: {joint_names: ${ARM_JOINTS}, points: [
  {positions: [0.4, 0.3, -0.4, 0.5, 0.3], time_from_start: {sec: 2}},
  {positions: [0.0, 0.0, 0.0, 0.0, 0.0], time_from_start: {sec: 4}}]}}"
result="$(timeout $((TIMEOUT + 10)) ros2 action send_goal \
  /arm_controller/follow_joint_trajectory control_msgs/action/FollowJointTrajectory "${goal}" 2>&1)"
echo "${result}" | grep -q "SUCCEEDED" || { echo "${result}" >&2; fail "trajectory did not succeed"; }
echo "      OK"

echo "[4/4] Joint positions after the trajectory:"
timeout "${TIMEOUT}" ros2 topic echo --once --field position /joint_states sensor_msgs/msg/JointState \
  | sed 's/^/      /'

echo "PASS"
