#!/usr/bin/env python3
"""roll_right: curve the robot to the right while rolling, by spinning the
left-side arms (A, C) faster than the right-side arms (B, D). Mirror of
roll_left. Once already folded into the wheel/rolling shape (run
transform_to_roll first).

Usage:
    ros2 run gelinder_control roll_right
    ros2 run gelinder_control roll_right --ros-args -p speed:=1.0 -p turn_ratio:=0.4 -p duration_sec:=4.0

Parameters: same as roll_left, but turn_ratio scales the RIGHT side (B, D)
instead of the left.
"""

from gelinder_control.rolling_node_base import RollingNodeBase, run_rolling_node


class RollRight(RollingNodeBase):
    def __init__(self):
        super().__init__("roll_right", default_speed=1.0)
        self.declare_parameter("turn_ratio", 0.4)
        turn_ratio = self.get_parameter("turn_ratio").value

        # Left side (the outside of the turn) spins at full speed; right
        # side (the inside of the turn) spins slower, so the robot curves
        # right while still moving forward overall.
        self.left_scale = 1.0
        self.right_scale = turn_ratio


def main(args=None):
    run_rolling_node(RollRight)


if __name__ == "__main__":
    main()
