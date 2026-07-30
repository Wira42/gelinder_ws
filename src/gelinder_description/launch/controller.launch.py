"""(Re)spawn the Gelinder ros2_control controllers without restarting
Gazebo. Useful when you only need to reload/restart joint_state_broadcaster
or gelinder_arm_controller, e.g. after editing
config/gelinder_controllers.yaml.

Assumes a controller_manager is already running (started by Gazebo through
the gz_ros2_control plugin via gazebo.launch.py).

Usage:
    ros2 launch gelinder_description controller.launch.py
"""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
        output="screen",
    )

    arm_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["gelinder_arm_controller"],
        output="screen",
    )

    return LaunchDescription(
        [
            joint_state_broadcaster_spawner,
            arm_controller_spawner,
        ]
    )
