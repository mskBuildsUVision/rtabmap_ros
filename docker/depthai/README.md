# OAK-FFC-3P DepthAI Docker Setup

This document describes the Docker-based RTAB-Map stereo SLAM pipeline for the **Luxonis OAK-FFC-3P** camera on ROS 2 Jazzy.

## Overview

The setup builds on `introlab3it/rtabmap_ros:jazzy-latest` and adds:

- **depthai-core** (Luxonis C++ SDK)
- **depthai-ros** (`depthai_ros_driver`, `depthai_bridge`, etc.)
- Local **rtabmap_ros** checkout as a colcon overlay
- OAK-FFC-3P camera config, camera_info publisher, and startup script

The pipeline is **stereo visual SLAM** (not RGB-D): left/right mono streams feed RTAB-Map stereo odometry and mapping.

## Quick Start

From the repo root:

```bash
# Build
docker build -f Dockerfile.depthai -t rtabmap-depthai:jazzy .

# Allow GUI from container (on host, once per session)
xhost +local:docker

# Run full SLAM (driver + camera_info + RTAB-Map + rtabmap_viz)
docker run -it --rm --name rtabmap_oak \
  --network host --privileged \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v /dev/bus/usb:/dev/bus/usb \
  rtabmap-depthai:jazzy \
  /config/start_slam.sh
```

Alternative: launch via the ROS launch file (same stack, single command):

```bash
docker run -it --rm --name rtabmap_oak \
  --network host --privileged \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v /dev/bus/usb:/dev/bus/usb \
  rtabmap-depthai:jazzy \
  ros2 launch rtabmap_examples depthai_ffc.launch.py \
    approx_sync:=true approx_sync_max_interval:=0.05
```

## Files

| File | Purpose |
|------|---------|
| `Dockerfile.depthai` | Image build definition |
| `docker/depthai/oak_ffc_stereo.yaml` | DepthAI driver params (STEREO pipeline, socket IDs, resolution) |
| `docker/depthai/pub_camera_info.py` | Publishes synced `/oak/*/camera_info_cal` from image timestamps |
| `docker/depthai/start_slam.sh` | Starts driver → camera_info → RTAB-Map in sequence |
| `rtabmap_examples/launch/depthai_ffc.launch.py` | Launch-file equivalent of the startup script |

Config files are copied into the image at `/config/` during build.

## Pipeline

```
OAK-FFC-3P (USB)
       │
       ▼
depthai_ros_driver (camera.launch.py)
       │
       ├── /oak/left/image_raw
       ├── /oak/right/image_raw
       └── /oak/left|right/camera_info  (empty — no EEPROM calibration)
       │
       ▼
pub_camera_info.py
       │
       ├── /oak/left/camera_info_cal   (stamped from left image header)
       └── /oak/right/camera_info_cal  (stamped from right image header)
       │
       ▼
rtabmap_launch (stereo mode)
       │
       ├── stereo_odometry  → /odom
       ├── rtabmap          → /map, /cloud_map, ...
       └── rtabmap_viz      → GUI
```

## Key Parameters

These were tuned during bring-up:

| Parameter | Value | Why |
|-----------|-------|-----|
| `frame_id` | `oak_left_camera_optical_frame` | Matches camera_info headers; avoids missing TF for `oak-d-base-frame` |
| `approx_sync` | `true` | Left/right timestamps differ ~33 ms; exact sync drops all frames |
| `approx_sync_max_interval` | `0.05` | Wide enough for OAK-FFC stereo pair skew |
| `i_pipeline_type` | `STEREO` | OAK-FFC-3P has two mono cameras, not RGB-D |
| `i_board_socket_id` | left=1, right=2 | FFC camera socket mapping |

## Issues Fixed During Bring-Up

### 1. Dockerfile heredoc parse error

Inline `RUN cat << 'EOF'` blocks failed because BuildKit requires heredoc syntax immediately after `RUN`:

```dockerfile
RUN <<'EOF'
cat > /path <<'EOT'
...
EOT
EOF
```

**Resolution:** Moved config into real files under `docker/depthai/` and `COPY` them into the image.

### 2. Wrong camera model (OAK-D vs OAK-FFC-3P)

The existing `depthai.launch.py` targets **OAK-D** via `depthai_examples/stereo_inertial_node.launch.py` with topics like `/right/image_rect`. OAK-FFC-3P uses `depthai_ros_driver` with `/oak/left|right/image_raw`.

**Resolution:** Added `depthai_ffc.launch.py` and `start_slam.sh` wired to OAK-FFC topics.

### 3. Missing `libsdformat14.so.14` / robot_state_publisher crash

The base image's `ros-jazzy-sdformat-urdf` plugin fails to load, which can abort the composable container hosting the OAK driver.

**Resolution:** Dockerfile removes `ros-jazzy-sdformat-urdf` (SDF parsing not needed for plain URDF/Xacro).

### 4. Empty camera_info (no EEPROM calibration)

Driver logs: `No calibration for socket 1/2! Publishing empty camera_info.`

**Resolution:** `pub_camera_info.py` subscribes to image streams and republishes `camera_info_cal` with matching timestamps and approximate intrinsics (fx = 0.8 × width, baseline tx = −fx × 0.075 for right camera).

### 5. RTAB-Map not receiving data / no video in viz

Two causes:

- **Exact sync** (`approx_sync:=false`) rejected frames because left/right stamps differ by ~33 ms.
- **Missing TF** when `frame_id:=oak-d-base-frame` (frame does not exist in TF tree).

**Resolution:** Use `approx_sync:=true`, `approx_sync_max_interval:=0.05`, and `frame_id:=oak_left_camera_optical_frame`.

### 6. Docker build COPY failures

`.dockerignore` excluded the entire `docker/` directory.

**Resolution:** Added `!docker/depthai/**` exception so config files are included in the build context.

## Debugging

Inside the running container:

```bash
# Check image streams
ros2 topic hz /oak/left/image_raw
ros2 topic hz /oak/right/image_raw

# Check synced camera_info
ros2 topic hz /oak/left/camera_info_cal
ros2 topic hz /oak/right/camera_info_cal

# View raw image (requires rqt_image_view in image)
ros2 run rqt_image_view rqt_image_view

# List OAK topics
ros2 topic list | grep oak
```

Expected rates: images ~16–26 Hz, camera_info_cal ~30 Hz.

## Not OAK-D

Do **not** use these for OAK-FFC-3P:

```bash
# Wrong — OAK-D RGB-D pipeline
ros2 launch rtabmap_examples depthai.launch.py camera_model:=OAK-D
ros2 launch rtabmap_examples depthai_color.launch.py camera_model:=OAK-D
```

Use `depthai_ffc.launch.py` or `/config/start_slam.sh` instead.

## Future Improvements

- Load real camera calibration from EEPROM or a calibration file instead of approximate intrinsics in `pub_camera_info.py`
- Add static TF or fix `robot_state_publisher` if a full device URDF/TF tree is needed
- Tune `approx_sync_max_interval` once hardware sync behavior is confirmed
