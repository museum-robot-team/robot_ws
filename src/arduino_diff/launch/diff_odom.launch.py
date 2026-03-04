from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package="arduino_diff",
            executable="diff_odom",
            output="screen"
        )
    ])