"""Convenience launch file: fold into the wheel shape (transform_to_roll)
and then immediately start rolling forward (roll_forward), in one command.

This is purely a convenience wrapper. The mode nodes are also perfectly
usable standalone:
    ros2 run gelinder_control transform_to_roll
    ros2 run gelinder_control roll_forward
    ros2 run gelinder_control roll_left
    ros2 run gelinder_control roll_right
    ros2 run gelinder_control roll_center

Usage:
    ros2 launch gelinder_control transform_and_roll.launch.py
    ros2 launch gelinder_control transform_and_roll.launch.py speed:=2.0 duration_sec:=5.0
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    speed_arg = DeclareLaunchArgument(
        name="speed", default_value="1.0", description="Wheel speed (rad/s) for rolling forward"
    )
    duration_arg = DeclareLaunchArgument(
        name="duration_sec",
        default_value="0.0",
        description="How long to roll forward, in seconds (0 = until Ctrl+C)",
    )

    transform_process = ExecuteProcess(
        cmd=["ros2", "run", "gelinder_control", "transform_to_roll"],
        output="screen",
    )

    roll_forward_process = ExecuteProcess(
        cmd=[
            "ros2", "run", "gelinder_control", "roll_forward",
            "--ros-args",
            "-p", ["speed:=", LaunchConfiguration("speed")],
            "-p", ["duration_sec:=", LaunchConfiguration("duration_sec")],
        ],
        output="screen",
    )

    # Only start roll_forward once transform_to_roll has finished (it exits
    # on its own after the fold trajectory completes).
    start_rolling_after_transform = RegisterEventHandler(
        OnProcessExit(
            target_action=transform_process,
            on_exit=[roll_forward_process],
        )
    )

    return LaunchDescription(
        [
            speed_arg,
            duration_arg,
            transform_process,
            start_rolling_after_transform,
        ]
    )
