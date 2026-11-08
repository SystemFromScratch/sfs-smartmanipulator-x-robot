# Copyright 2026 Anton Vynohradov
# SPDX-License-Identifier: Apache-2.0
"""Robot PC bringup: robot_state_publisher, ros2_control and the controllers.

    ros2 launch smartmanipulator_x_bringup robot.launch.py use_mock_hardware:=true

No RViz or MoveIt here: they run on the Operator PC and reach this host over
ROS 2 DDS.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def _require_mock_hardware(context, *args, **kwargs):
    value = LaunchConfiguration("use_mock_hardware").perform(context).strip().lower()
    if value not in ("true", "1", "yes"):
        raise RuntimeError(
            "use_mock_hardware:=false is not available yet: the real-hardware "
            "ros2_control configuration (SmartFusion2 / Doppelstep over "
            "dynamixel_hardware_interface) has not been verified. "
            "See docs/dynamixel/compatibility-spec.md."
        )
    return []


def generate_launch_description():
    use_mock_hardware = LaunchConfiguration("use_mock_hardware")

    robot_description = ParameterValue(
        Command([
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution([
                FindPackageShare("smartmanipulator_x_description"),
                "urdf",
                "smartmanipulator_x.urdf.xacro",
            ]),
            " use_mock_hardware:=",
            use_mock_hardware,
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
        parameters=[controllers_file],
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
            "use_mock_hardware",
            default_value="true",
            description="Use mock_components/GenericSystem instead of the real controller.",
        ),
        OpaqueFunction(function=_require_mock_hardware),
        robot_state_publisher,
        control_node,
        spawner,
    ])
