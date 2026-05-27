#!/bin/bash
set -e

source /opt/ros/jazzy/setup.bash
[ -f /root/ros2_ws/install/setup.bash ] && source /root/ros2_ws/install/setup.bash

echo "[1/3] Starting OAK-FFC driver..."
ros2 launch depthai_ros_driver camera.launch.py \
  params_file:=/config/oak_ffc_stereo.yaml &

echo "Waiting 8s for camera to initialise..."
sleep 8

echo "[2/3] Starting camera_info publisher..."
python3 /config/pub_camera_info.py &

sleep 2

echo "[3/3] Starting RTAB-Map..."
exec ros2 launch rtabmap_launch rtabmap.launch.py \
  stereo:=true \
  left_image_topic:=/oak/left/image_raw \
  right_image_topic:=/oak/right/image_raw \
  left_camera_info_topic:=/oak/left/camera_info_cal \
  right_camera_info_topic:=/oak/right/camera_info_cal \
  frame_id:=oak_left_camera_optical_frame \
  approx_sync:=true \
  approx_sync_max_interval:=0.05 \
  rtabmap_args:="--delete_db_on_start" \
  rtabmapviz:=true \
  rviz:=false
