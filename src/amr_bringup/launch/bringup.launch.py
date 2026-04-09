import os
from launch import LaunchDescription
from launch.actions import (
    IncludeLaunchDescription, DeclareLaunchArgument, TimerAction
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    slam_mode    = LaunchConfiguration('slam_mode',    default='mapping')

    # ── Package paths ────────────────────────────────────────────────────────
    pkg_gazebo  = get_package_share_directory('amr_gazebo')
    pkg_desc    = get_package_share_directory('amr_description')
    pkg_slam    = get_package_share_directory('amr_slam')
    pkg_nav     = get_package_share_directory('amr_navigation')

    # ── 1. Gazebo world ──────────────────────────────────────────────────────
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo, 'launch', 'gazebo.launch.py')
        )
    )

    # ── 2. Robot state publisher ─────────────────────────────────────────────
    robot_description_path = os.path.join(
        pkg_desc, 'urdf', 'robot.urdf.xacro'
    )
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'use_sim_time': use_sim_time,
            'robot_description': open(robot_description_path).read()
        }],
        output='screen'
    )

    # ── 3. Spawn robot in Gazebo ─────────────────────────────────────────────
    spawn_robot = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-entity', 'amr_robot',
            '-topic', 'robot_description',
            '-x', '0.0', '-y', '0.0', '-z', '0.05'
        ],
        output='screen'
    )

    # ── 4. SLAM Toolbox (delayed 3s to let Gazebo fully load) ────────────────
    slam_launch = TimerAction(
        period=3.0,
        actions=[IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_slam, 'launch', 'slam.launch.py')
            ),
            launch_arguments={
                'use_sim_time': use_sim_time,
                'slam_mode': slam_mode
            }.items()
        )]
    )

    # ── 5. Nav2 (delayed 5s to let SLAM initialise) ──────────────────────────
    nav2_launch = TimerAction(
        period=5.0,
        actions=[IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_nav, 'launch', 'navigation.launch.py')
            ),
            launch_arguments={'use_sim_time': use_sim_time}.items()
        )]
    )

    # ── 6. RViz2 ─────────────────────────────────────────────────────────────
    rviz_config = os.path.join(pkg_desc, 'rviz', 'robot_view.rviz')
    rviz = TimerAction(
        period=6.0,
        actions=[Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', rviz_config],
            parameters=[{'use_sim_time': use_sim_time}],
            output='screen'
        )]
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('slam_mode',    default_value='mapping'),
        gazebo_launch,
        robot_state_publisher,
        spawn_robot,
        slam_launch,
        nav2_launch,
        rviz,
    ])