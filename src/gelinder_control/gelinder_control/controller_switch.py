"""Shared helper for activating/deactivating ros2_control controllers from
a Python node, by calling the controller_manager's SwitchController
service -- the same mechanism behind `ros2 control switch_controllers`.

Used by every node in this package so that switching between the position
controller (gelinder_arm_controller) and the velocity controller
(gelinder_velocity_controller) is consistent and only written once.
"""

from controller_manager_msgs.srv import SwitchController


def switch_controllers(node, activate, deactivate, timeout_sec=5.0):
    """Call /controller_manager/switch_controller to activate one set of
    controllers and deactivate another.

    Args:
        node: an rclpy Node to create the client/log from.
        activate: list[str] of controller names to activate.
        deactivate: list[str] of controller names to deactivate.
        timeout_sec: how long to wait for the service to appear.

    Returns:
        True if the switch was accepted (service replied ok=True),
        False otherwise (service unavailable, call failed, or rejected).
    """
    client = node.create_client(SwitchController, "/controller_manager/switch_controller")

    if not client.wait_for_service(timeout_sec=timeout_sec):
        node.get_logger().error(
            "/controller_manager/switch_controller service not available. "
            "Is gazebo.launch.py (or ros2_control_node) running?"
        )
        return False

    request = SwitchController.Request()
    request.activate_controllers = activate
    request.deactivate_controllers = deactivate
    # STRICT means the call fails loudly if a requested controller doesn't
    # exist or can't be switched, instead of silently ignoring it.
    request.strictness = SwitchController.Request.STRICT
    request.activate_asap = True
    request.timeout = rclpy_duration_msg(timeout_sec)

    future = client.call_async(request)
    rclpy_spin_until_complete(node, future, timeout_sec)

    if future.result() is None:
        node.get_logger().error("switch_controller call did not complete (timed out).")
        return False

    if not future.result().ok:
        node.get_logger().error(
            f"switch_controller rejected: activate={activate} deactivate={deactivate}"
        )
        return False

    node.get_logger().info(f"Switched controllers: activated={activate}, deactivated={deactivate}")
    return True


def rclpy_duration_msg(seconds):
    from builtin_interfaces.msg import Duration

    sec = int(seconds)
    nanosec = int((seconds - sec) * 1e9)
    return Duration(sec=sec, nanosec=nanosec)


def rclpy_spin_until_complete(node, future, timeout_sec):
    import rclpy

    rclpy.spin_until_future_complete(node, future, timeout_sec=timeout_sec)
