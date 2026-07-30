"""Shared base class for the continuous-rolling nodes (roll_forward,
roll_left, roll_right).

All three follow the same pattern:
  1. Make sure gelinder_velocity_controller is active (and
     gelinder_arm_controller is not -- they share command interfaces).
  2. Publish a constant Float64MultiArray to
     /gelinder_velocity_controller/commands at a fixed rate, for a given
     duration (or forever, if duration_sec <= 0).
  3. On exit (duration elapsed, or Ctrl+C), publish all-zero velocities
     once so the robot coasts to a stop instead of spinning forever
     un-commanded.

NOTE: this assumes the robot is ALREADY folded into the wheel/rolling
shape (run `ros2 run gelinder_control transform_to_roll` first). These
nodes only spin the joints; they don't change their shape.
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray

from gelinder_control.controller_switch import switch_controllers
from gelinder_control.rolling_config import JOINT_ORDER, build_velocity_command


class RollingNodeBase(Node):
    """node_name: unique ROS node name, e.g. 'roll_forward'.
    default_speed: default wheel speed (rad/s) used if the `speed` ROS
        parameter isn't overridden on the command line.
    """

    def __init__(self, node_name, default_speed):
        super().__init__(node_name)
        self.declare_parameter("speed", default_speed)
        self.declare_parameter("duration_sec", 0.0)  # <=0 means "run forever until Ctrl+C"
        self.declare_parameter("left_scale", 1.0)
        self.declare_parameter("right_scale", 1.0)
        self.declare_parameter("rate_hz", 20.0)

        self.speed = self.get_parameter("speed").value
        self.duration_sec = self.get_parameter("duration_sec").value
        self.left_scale = self.get_parameter("left_scale").value
        self.right_scale = self.get_parameter("right_scale").value
        self.rate_hz = self.get_parameter("rate_hz").value

        self._publisher = self.create_publisher(
            Float64MultiArray, "/gelinder_velocity_controller/commands", 10
        )
        self._elapsed = 0.0
        self._timer = None

    def start(self):
        self.get_logger().info("Activating velocity controller (gelinder_velocity_controller)...")
        ok = switch_controllers(
            self,
            activate=["gelinder_velocity_controller"],
            deactivate=["gelinder_arm_controller"],
        )
        if not ok:
            self.get_logger().error("Could not activate gelinder_velocity_controller. Aborting.")
            return False

        velocities = build_velocity_command(
            self.speed, left_scale=self.left_scale, right_scale=self.right_scale
        )
        self.get_logger().info(
            f"Rolling with joint velocities (rad/s), order {JOINT_ORDER}: "
            f"{[round(v, 3) for v in velocities]}"
        )
        if self.duration_sec > 0:
            self.get_logger().info(f"Will run for {self.duration_sec:.1f}s then stop.")
        else:
            self.get_logger().info("Running until Ctrl+C (no duration set).")

        period = 1.0 / self.rate_hz
        self._timer = self.create_timer(period, lambda: self._on_tick(velocities, period))
        return True

    def _on_tick(self, velocities, period):
        msg = Float64MultiArray()
        msg.data = velocities
        self._publisher.publish(msg)

        if self.duration_sec > 0:
            self._elapsed += period
            if self._elapsed >= self.duration_sec:
                self.get_logger().info("Duration elapsed, stopping.")
                self.stop_and_shutdown()

    def stop_and_shutdown(self):
        """Publish zero velocity once, then ask rclpy to stop spinning."""
        zero_msg = Float64MultiArray()
        zero_msg.data = [0.0] * len(JOINT_ORDER)
        self._publisher.publish(zero_msg)
        if self._timer is not None:
            self._timer.cancel()
        raise SystemExit


def run_rolling_node(node_class):
    """Common main() body shared by all three rolling node scripts."""
    rclpy.init()
    node = node_class()
    try:
        if node.start():
            rclpy.spin(node)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        # Make a best-effort attempt to stop the wheels before shutting down,
        # in case we got here via Ctrl+C rather than stop_and_shutdown().
        try:
            zero_msg = Float64MultiArray()
            zero_msg.data = [0.0] * len(JOINT_ORDER)
            node._publisher.publish(zero_msg)
        except Exception:
            pass
        node.destroy_node()
        rclpy.shutdown()
