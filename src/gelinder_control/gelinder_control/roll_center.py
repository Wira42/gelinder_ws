#!/usr/bin/env python3
"""roll_center: roll straight ahead (the "tengah" / center direction,
as opposed to roll_left / roll_right). Functionally identical to
roll_forward -- both sides spin at the same speed -- provided as a
separate command so the kanan/kiri/tengah naming from the task is
available directly via `ros2 run`.

Usage:
    ros2 run gelinder_control roll_center
    ros2 run gelinder_control roll_center --ros-args -p speed:=2.0 -p duration_sec:=5.0

Parameters: same as roll_forward.
"""

from gelinder_control.rolling_node_base import RollingNodeBase, run_rolling_node


class RollCenter(RollingNodeBase):
    def __init__(self):
        super().__init__("roll_center", default_speed=1.0)
        self.left_scale = 1.0
        self.right_scale = 1.0


def main(args=None):
    run_rolling_node(RollCenter)


if __name__ == "__main__":
    main()
