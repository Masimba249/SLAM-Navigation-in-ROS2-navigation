from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='amr_explore',
            executable='frontier_explorer',
            name='frontier_explorer',
            output='screen',
            parameters=[{'use_sim_time': True}],
        )
    ])
