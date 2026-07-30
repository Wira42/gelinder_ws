"""Spawn the Gelinder robot into Gazebo Fortress (gz-sim) and bring up
ros2_control (joint_state_broadcaster + the trajectory/position controllers
defined in config/gelinder_controllers.yaml).

The actual controller configuration is loaded from the gz_ros2_control
plugin declared inside urdf/gelinder.gazebo.xacro -- this launch file just
starts the simulator, spawns the model, bridges /clock, and spawns the
ros2_control controllers on top of it.

Usage:
    ros2 launch gelinder_description gazebo.launch.py
    ros2 launch gelinder_description gazebo.launch.py world:=empty.sdf
"""

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_gelinder_description = get_package_share_directory("gelinder_description")
    pkg_ros_gz_sim = get_package_share_directory("ros_gz_sim")

    default_model_path = os.path.join(
        pkg_gelinder_description, "urdf", "gelinder.urdf.xacro"
    )

    # The URDF references meshes with "package://gelinder_description/meshes/...".
    # ros_gz_sim/sdformat rewrites that to "model://gelinder_description/meshes/...",
    # which Gazebo resolves by searching GZ_SIM_RESOURCE_PATH for a folder named
    # "gelinder_description". That folder is the parent of pkg_gelinder_description
    # itself (i.e. the colcon install share/ directory), so we add it here.
    # Without this, Gazebo prints "Unable to find file with URI [model://...]"
    # and the robot spawns with no visible geometry.
    gz_resource_path = SetEnvironmentVariable(
        name="GZ_SIM_RESOURCE_PATH",
        value=os.path.dirname(pkg_gelinder_description),
    )

    model_arg = DeclareLaunchArgument(
        name="model",
        default_value=default_model_path,
        description="Absolute path to the robot xacro/URDF file",
    )
    world_arg = DeclareLaunchArgument(
        name="world",
        default_value="empty.sdf",
        description="Gazebo world file (name of a world shipped with ros_gz_sim, or an absolute path)",
    )

    # IMPORTANT: see display.launch.py for why this must be wrapped in
    # ParameterValue(..., value_type=str) -- without it, launch_ros tries
    # to parse the xacro-expanded URDF string as YAML and throws
    # "Unable to parse the value of parameter robot_description as yaml".
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

    # 1. Start Gazebo Fortress (server + GUI) with the requested world.
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, "launch", "gz_sim.launch.py")
        ),
        launch_arguments={"gz_args": [LaunchConfiguration("world"), " -r"]}.items(),
    )

    # 2. Publish robot_description and the live TF tree from /joint_states.
    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[robot_description, {"use_sim_time": True}],
    )

    # 3. Spawn the robot model into the running Gazebo world by reading
    #    /robot_description (published by robot_state_publisher above).
    spawn_entity_node = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-topic",
            "robot_description",
            "-name",
            "gelinder",
            "-z",
            "0.05",
        ],
        output="screen",
    )

    # 4. Bridge the Gazebo simulation clock to ROS 2 -- required for
    #    controller_manager / ros2_control to run correctly under
    #    use_sim_time.
    clock_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="clock_bridge",
        arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],
        output="screen",
    )

    # 5. Spawn the ros2_control controllers once the controller_manager
    #    (started inside Gazebo by the gz_ros2_control plugin) is up.
    #    A short delay avoids racing the spawner against gz_ros2_control's
    #    controller_manager startup.
    joint_state_broadcaster_spawner = TimerAction(
        period=5.0,
        actions=[
            Node(
                package="controller_manager",
                executable="spawner",
                arguments=["joint_state_broadcaster"],
                output="screen",
            )
        ],
    )

    arm_controller_spawner = TimerAction(
        period=7.0,
        actions=[
            Node(
                package="controller_manager",
                executable="spawner",
                arguments=["gelinder_arm_controller"],
                output="screen",
            )
        ],
    )

    # gelinder_velocity_controller claims the same command interfaces as
    # gelinder_arm_controller, so it is loaded here but kept INACTIVE.
    # The gelinder_control mode nodes (roll_forward/roll_left/roll_right/
    # roll_center) switch it on -- and gelinder_arm_controller off -- via
    # /controller_manager/switch_controller when a rolling mode is run.
    velocity_controller_spawner = TimerAction(
        period=7.0,
        actions=[
            Node(
                package="controller_manager",
                executable="spawner",
                arguments=["gelinder_velocity_controller", "--inactive"],
                output="screen",
            )
        ],
    )

    return LaunchDescription(
        [
            gz_resource_path,
            model_arg,
            world_arg,
            gz_sim,
            robot_state_publisher_node,
            clock_bridge,
            spawn_entity_node,
            joint_state_broadcaster_spawner,
            arm_controller_spawner,
            velocity_controller_spawner,
        ]
    )
