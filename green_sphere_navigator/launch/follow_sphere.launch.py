import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    turtlebot3_gazebo_dir = get_package_share_directory('turtlebot3_gazebo')
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(turtlebot3_gazebo_dir, 'launch', 'empty_world.launch.py')
        )
    )

    pkg_share = get_package_share_directory('green_sphere_navigator')
    sphere_path = os.path.join(pkg_share, 'models', 'sphere.sdf')

    spawn_sphere = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-file', sphere_path,
            '-entity', 'green_sphere',
            '-x', '1.5', '-y', '0.0', '-z', '0.5'
        ],
        output='screen'
    )

    vision_node = Node(
        package='green_sphere_navigator',
        executable='vision_node',
        name='vision_node',
        output='screen',
        remappings=[
            ('image_raw', '/camera/image_raw')
        ],
        parameters=[{
            'hue_low': 30, 'hue_high': 90,
            'sat_low': 30, 'sat_high': 255,
            'val_low': 30, 'val_high': 255,
            'min_contour_area': 30,
            'show_debug_window': True
        }]
    )

    controller_node = Node(
        package='green_sphere_navigator',
        executable='controller_node',
        name='controller_node',
        output='screen',
        parameters=[{
            'Kp': 0.003,
            'error_tolerance': 40.0,
            'stop_distance': 0.35,
            'search_rot_speed': 0.3,
            'linear_speed': 0.12,
            'max_angular': 0.5
        }]
    )

    return LaunchDescription([
        gazebo_launch,
        TimerAction(period=5.0, actions=[spawn_sphere, vision_node, controller_node])
    ])
