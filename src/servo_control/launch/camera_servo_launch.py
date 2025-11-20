from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='servo_control',
            executable='servo_node',
            name='servo_node',
            output='screen'
        ),
        Node(
            package='servo_control',
            executable='camera_tracker',
            name='camera_tracker',
            output='screen'
        ),
    ])