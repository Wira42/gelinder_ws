#!/usr/bin/env python3
"""roll_left: curve the robot to the left while rolling, by spinning the
right-side arms (B, D) faster than the left-side arms (A, C) -- the same
differential-drive trick used by skid-steer robots. Once already folded
into the wheel/rolling shape (run transform_to_roll first).

Usage:
    ros2 run gelinder_control roll_left
    ros2 run gelinder_control roll_left --ros-args -p speed:=1.0 -p turn_ratio:=0.4 -p duration_sec:=4.0

Parameters:
    speed (float, default 1.0): wheel angular speed in rad/s for the
        faster (right) side. Negative values turn while rolling backward.
    turn_ratio (float, default 0.4): speed multiplier applied to the
        LEFT side (A, C) relative to `speed`. 1.0 = no turn (same as
        roll_forward); 0.0 = the left side stays still and the robot
        pivots in place; values in between curve left while still
        moving forward. Use a small negative value to spin the left side
        backward for a tighter (in-place-ish) turn.
    duration_sec (float, default 0.0): how long to turn, in seconds.
        0 or negative means "run forever until Ctrl+C".
    rate_hz (float, default 20.0): how often to (re-)publish the velocity
        command.
"""

from gelinder_control.rolling_node_base import RollingNodeBase, run_rolling_node


class RollLeft(RollingNodeBase):
    def __init__(self):
        super().__init__("roll_left", default_speed=1.0)
        self.declare_parameter("turn_ratio", 0.4)
        turn_ratio = self.get_parameter("turn_ratio").value

        # Right side (the outside of the turn) spins at full speed; left
        # side (the inside of the turn) spins slower, so the robot curves
        # left while still moving forward overall.
        self.right_scale = 1.0
        self.left_scale = turn_ratio


def main(args=None):
    run_rolling_node(RollLeft)


if __name__ == "__main__":
    main()
