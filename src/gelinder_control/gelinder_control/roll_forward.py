#!/usr/bin/env python3
"""roll_forward: spin all 12 joints at the same speed so the robot rolls
straight forward, once already folded into the wheel/rolling shape.

Run `ros2 run gelinder_control transform_to_roll` first.

Usage:
    ros2 run gelinder_control roll_forward
    ros2 run gelinder_control roll_forward --ros-args -p speed:=2.0 -p duration_sec:=5.0

Parameters:
    speed (float, default 1.0): wheel angular speed in rad/s. Negative
        values roll backward.
    duration_sec (float, default 0.0): how long to roll, in seconds.
        0 or negative means "run forever until Ctrl+C".
    rate_hz (float, default 20.0): how often to (re-)publish the velocity
        command.
"""

import rclpy

from gelinder_control.rolling_node_base import RollingNodeBase, run_rolling_node


class RollForward(RollingNodeBase):
    def __init__(self):
        super().__init__("roll_forward", default_speed=1.0)
        # Straight ahead: both sides spin at full requested speed.
        self.left_scale = 1.0
        self.right_scale = 1.0


def main(args=None):
    run_rolling_node(RollForward)


if __name__ == "__main__":
    main()
