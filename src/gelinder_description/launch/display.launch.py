"""Display the Gelinder robot model in RViz, with joint_state_publisher_gui
providing manual sliders for all 12 joints (no physics, no Gazebo).

Usage:
    ros2 launch gelinder_description display.launch.py
    ros2 launch gelinder_description display.launch.py gui:=false
"""

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_share = get_package_share_directory("gelinder_description")

    default_model_path = os.path.join(pkg_share, "urdf", "gelinder.urdf.xacro")
    default_rviz_config_path = os.path.join(pkg_share, "rviz", "gelinder.rviz")

    model_arg = DeclareLaunchArgument(
        name="model",
        default_value=default_model_path,
        description="Absolute path to the robot xacro/URDF file",
    )
    gui_arg = DeclareLaunchArgument(
        name="gui",
        default_value="true",
        description="Show joint_state_publisher_gui sliders to manually move the joints",
    )
    rviz_config_arg = DeclareLaunchArgument(
        name="rvizconfig",
        default_value=default_rviz_config_path,
        description="Absolute path to the RViz config file",
    )

    # IMPORTANT: the output of `xacro <file>` is a long XML/URDF string.
    # launch_ros tries to auto-parse plain string parameter values as YAML,
    # and a URDF full of colons/brackets is not valid YAML, which throws
    # "Unable to parse the value of parameter robot_description as yaml".
    # Wrapping it in ParameterValue(..., value_type=str) forces launch_ros
    # to treat it as a raw string and skip the YAML parsing attempt.
    robot_description = {
        "robot_description": ParameterValue(
            Command(
                [
                    PathJoinSubstitution([FindExecutable(name="xacro")]),
                    " ",
                    LaunchConfiguration("model"),
                ]
            ),
            value_type=str,
        )
    }

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[robot_description],
    )

    joint_state_publisher_gui_node = Node(
        package="joint_state_publisher_gui",
        executable="joint_state_publisher_gui",
        condition=IfCondition(LaunchConfiguration("gui")),
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", LaunchConfiguration("rvizconfig")],
    )

    return LaunchDescription(
        [
            model_arg,
            gui_arg,
            rviz_config_arg,
            joint_state_publisher_gui_node,
            robot_state_publisher_node,
            rviz_node,
        ]
    )
