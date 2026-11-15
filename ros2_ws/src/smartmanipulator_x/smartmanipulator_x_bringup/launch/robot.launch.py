# Copyright 2026 Anton Vynohradov
# SPDX-License-Identifier: Apache-2.0
"""Robot PC bringup: robot_state_publisher, ros2_control and the controllers.

    ros2 launch smartmanipulator_x_bringup robot.launch.py                     # mock joints
    ros2 launch smartmanipulator_x_bringup robot.launch.py hardware:=sil       # SIL bus
    ros2 launch smartmanipulator_x_bringup robot.launch.py hardware:=sil \\
        port_name:=/dev/ttyDXL baud_rate:=1000000

hardware:=real is refused until the bench stage is verified (one real doppelstep
drive, docs/plan/doppelstep-cm4.md). No RViz or MoveIt here: they run on the
Operator PC and reach this host over ROS 2 DDS.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare

HARDWARE = ("mock", "sil", "real")


def _check_hardware(context, *args, **kwargs):
    legacy = LaunchConfiguration("use_mock_hardware").perform(context).strip().lower()
    if legacy and legacy not in ("true", "1", "yes"):
        raise RuntimeError(
            "use_mock_hardware is replaced by hardware:=mock|sil|real; "
            "use hardware:=sil for the simulated doppelstep drives."
        )
    hardware = LaunchConfiguration("hardware").perform(context).strip().lower()
    if hardware not in HARDWARE:
        raise RuntimeError(f"hardware:={hardware} is unknown; use one of {', '.join(HARDWARE)}.")
    if hardware == "real":
        raise RuntimeError(
            "hardware:=real is not available yet: the real-hardware path (doppelstep over "
            "dynamixel_hardware_interface) is verified first in SIL and on the bench. "
            "See docs/plan/doppelstep-cm4.md and docs/dynamixel/compatibility-spec.md."
        )
    return []


def generate_launch_description():
    hardware = LaunchConfiguration("hardware")

    robot_description = ParameterValue(
        Command([
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution([
                FindPackageShare("smartmanipulator_x_description"),
                "urdf",
                "smartmanipulator_x.urdf.xacro",
            ]),
            " hardware:=", hardware,
            " port_name:=", LaunchConfiguration("port_name"),
            " baud_rate:=", LaunchConfiguration("baud_rate"),
        ]),
        value_type=str,
    )

    controllers_file = PathJoinSubstitution([
        FindPackageShare("smartmanipulator_x_config"), "config", "controllers.yaml",
    ])

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[{"robot_description": robot_description}],
    )

    control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        output="screen",
        parameters=[
            controllers_file,
            {"update_rate": ParameterValue(LaunchConfiguration("update_rate"), value_type=int)},
        ],
        remappings=[("~/robot_description", "/robot_description")],
    )

    spawner = Node(
        package="controller_manager",
        executable="spawner",
        output="screen",
        arguments=[
            "joint_state_broadcaster",
            "arm_controller",
            "gripper_controller",
            "--controller-manager", "/controller_manager",
        ],
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            "hardware",
            default_value="mock",
            description="Arm joints: mock (simulated in ros2_control), sil (simulated "
                        "doppelstep drives on the virtual bus) or real (not available yet).",
        ),
        DeclareLaunchArgument(
            "port_name", default_value="/dev/ttyDXL",
            description="Serial device of the DYNAMIXEL bus (sil, real).",
        ),
        DeclareLaunchArgument(
            "baud_rate", default_value="1000000",
            description="Bus baud rate (sil, real); must match the drives.",
        ),
        DeclareLaunchArgument(
            "update_rate", default_value="100",
            description="controller_manager update rate in Hz (SIL uses 50: the "
                        "simulated drives answer a Sync Read in 10-20 ms).",
        ),
        DeclareLaunchArgument(
            "use_mock_hardware", default_value="",
            description="Deprecated, use hardware:=mock|sil|real.",
        ),
        OpaqueFunction(function=_check_hardware),
        robot_state_publisher,
        control_node,
        spawner,
    ])
