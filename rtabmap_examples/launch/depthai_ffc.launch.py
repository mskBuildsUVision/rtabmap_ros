#!/usr/bin/env python3
# Requirements:
#   An OAK-FFC-3P camera
#   Install depthai-ros package (https://github.com/luxonis/depthai-ros).
# Example:
#   $ ros2 launch rtabmap_examples depthai_ffc.launch.py
#
# Description: DepthAI OAK-FFC-3P stereo feed into rtabmap_launch.

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    params_file = LaunchConfiguration('params_file')
    frame_id = LaunchConfiguration('frame_id')
    approx_sync = LaunchConfiguration('approx_sync')
    approx_sync_max_interval = LaunchConfiguration('approx_sync_max_interval')
    rtabmapviz = LaunchConfiguration('rtabmapviz')
    rviz = LaunchConfiguration('rviz')

    return LaunchDescription([
        DeclareLaunchArgument(
            'params_file',
            default_value='/config/oak_ffc_stereo.yaml',
            description='DepthAI driver parameters for OAK-FFC-3P.',
        ),
        DeclareLaunchArgument(
            'frame_id',
            default_value='oak_left_camera_optical_frame',
            description='Base frame for the OAK device.',
        ),
        DeclareLaunchArgument(
            'approx_sync',
            default_value='false',
            description='Use approximate sync for stereo topics.',
        ),
        DeclareLaunchArgument(
            'approx_sync_max_interval',
            default_value='0.01',
            description='Max interval for approximate sync (seconds).',
        ),
        DeclareLaunchArgument(
            'rtabmapviz',
            default_value='true',
            description='Enable rtabmapviz.',
        ),
        DeclareLaunchArgument(
            'rviz',
            default_value='false',
            description='Enable rviz.',
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                os.path.join(
                    get_package_share_directory('depthai_ros_driver'),
                    'launch',
                    'camera.launch.py',
                )
            ]),
            launch_arguments={'params_file': params_file}.items(),
        ),
        ExecuteProcess(
            cmd=['python3', '/config/pub_camera_info.py'],
            output='screen',
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                os.path.join(
                    get_package_share_directory('rtabmap_launch'),
                    'launch',
                    'rtabmap.launch.py',
                )
            ]),
            launch_arguments={
                'stereo': 'true',
                'left_image_topic': '/oak/left/image_raw',
                'right_image_topic': '/oak/right/image_raw',
                'left_camera_info_topic': '/oak/left/camera_info_cal',
                'right_camera_info_topic': '/oak/right/camera_info_cal',
                'frame_id': frame_id,
                'approx_sync': approx_sync,
                'approx_sync_max_interval': approx_sync_max_interval,
                'rtabmapviz': rtabmapviz,
                'rviz': rviz,
                'rtabmap_args': '--delete_db_on_start',
            }.items(),
        ),
    ])
