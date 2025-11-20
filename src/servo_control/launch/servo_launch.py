from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='servo_control',
            executable='servo_node',
            name='servo_node',
            output='screen',
            emulate_tty=True
        )
    ])