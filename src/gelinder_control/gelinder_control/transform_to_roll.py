#!/usr/bin/env python3
"""transform_to_roll: fold all 12 joints of Gelinder to 0 rad, forming the
rolling/wheel shape, using the position-based joint trajectory controller.

This is meant to run BEFORE roll_forward / roll_left / roll_right, since
those expect the robot to already be folded into the wheel shape and only
spin the wheels from there.

What it does, step by step:
  1. Makes sure gelinder_arm_controller (position) is the active controller
     and gelinder_velocity_controller is not (they claim the same command
     interfaces, so only one can be active at a time).
  2. Sends a single-point JointTrajectory with all 12 joints target = 0.0
     rad, over TRANSFORM_DURATION_SEC seconds.
  3. Waits for the trajectory action to finish, then exits.

Usage:
    ros2 run gelinder_control transform_to_roll
    ros2 run gelinder_control transform_to_roll --ros-args -p duration_sec:=3.0
"""

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient

from control_msgs.action import FollowJointTrajectory
from trajectory_msgs.msg import JointTrajectoryPoint
from builtin_interfaces.msg import Duration

from gelinder_control.controller_switch import switch_controllers

JOINT_NAMES = [
    "A0", "A1", "A2",
    "B0", "B1", "B2",
    "C0", "C1", "C2",
    "D0", "D1", "D2",
]


class TransformToRoll(Node):
    def __init__(self):
        super().__init__("transform_to_roll")
        self.declare_parameter("duration_sec", 3.0)
        self.duration_sec = self.get_parameter("duration_sec").value

        self._action_client = ActionClient(
            self, FollowJointTrajectory, "/gelinder_arm_controller/follow_joint_trajectory"
        )

    def run(self):
        self.get_logger().info("Activating position controller (gelinder_arm_controller)...")
        ok = switch_controllers(
            self,
            activate=["gelinder_arm_controller"],
            deactivate=["gelinder_velocity_controller"],
        )
        if not ok:
            self.get_logger().error("Could not activate gelinder_arm_controller. Aborting.")
            return False

        self.get_logger().info("Waiting for follow_joint_trajectory action server...")
        if not self._action_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error(
                "Action server /gelinder_arm_controller/follow_joint_trajectory not available."
            )
            return False

        goal = FollowJointTrajectory.Goal()
        goal.trajectory.joint_names = JOINT_NAMES

        point = JointTrajectoryPoint()
        point.positions = [0.0] * len(JOINT_NAMES)
        sec = int(self.duration_sec)
        nanosec = int((self.duration_sec - sec) * 1e9)
        point.time_from_start = Duration(sec=sec, nanosec=nanosec)
        goal.trajectory.points = [point]

        self.get_logger().info(
            f"Sending goal: fold all 12 joints to 0.0 rad over {self.duration_sec:.1f}s ..."
        )
        send_goal_future = self._action_client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, send_goal_future, timeout_sec=5.0)
        goal_handle = send_goal_future.result()

        if goal_handle is None or not goal_handle.accepted:
            self.get_logger().error("Goal was rejected by the controller.")
            return False

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future, timeout_sec=self.duration_sec + 5.0)

        if result_future.result() is None:
            self.get_logger().error("Trajectory did not complete in time.")
            return False

        self.get_logger().info("Robot is now folded into the rolling/wheel shape.")
        return True


def main(args=None):
    rclpy.init(args=args)
    node = TransformToRoll()
    try:
        node.run()
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
