#!/usr/bin/env python3
#
# Workaround helper for OAK-D / OAK-FFC setups where the depthai-ros driver
# does NOT publish CameraInfo synchronized with the image timestamps. RTAB-Map
# needs CameraInfo with matching timestamps to compute stereo / projection, so
# we republish a synthetic CameraInfo per incoming image, copying the image's
# header (timestamp + frame_id) exactly.
#
# The intrinsics here are a rough estimate (fx ~ 0.8 * width, principal point
# at image center, plumb_bob with zero distortion) and the baseline is
# hard-coded to 7.5 cm (OAK-D / OAK-FFC). Replace with your calibrated values
# whenever you can.
#
# Subscribed topics:
#   /oak/left/image_raw   sensor_msgs/Image
#   /oak/right/image_raw  sensor_msgs/Image
#
# Published topics:
#   /oak/left/camera_info_cal   sensor_msgs/CameraInfo
#   /oak/right/camera_info_cal  sensor_msgs/CameraInfo
#
# Usage:
#   ros2 run rtabmap_examples pub_camera_info.py
import copy

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CameraInfo, Image


class CameraInfoPublisher(Node):
    def __init__(self):
        super().__init__('camera_info_publisher')
        self.left_pub  = self.create_publisher(CameraInfo, '/oak/left/camera_info_cal',  10)
        self.right_pub = self.create_publisher(CameraInfo, '/oak/right/camera_info_cal', 10)
        self.create_subscription(Image, '/oak/left/image_raw',  self.left_cb,  10)
        self.create_subscription(Image, '/oak/right/image_raw', self.right_cb, 10)

    def make_msg(self, img, side):
        msg = CameraInfo()
        msg.header = copy.deepcopy(img.header)
        msg.width  = img.width
        msg.height = img.height
        fx = img.width * 0.8
        cx = img.width  / 2.0
        cy = img.height / 2.0
        baseline = 0.075
        msg.distortion_model = 'plumb_bob'
        msg.d = [0.0, 0.0, 0.0, 0.0, 0.0]
        msg.k = [fx,  0.0,  cx,
                 0.0,  fx,  cy,
                 0.0, 0.0, 1.0]
        msg.r = [1.0, 0.0, 0.0,
                 0.0, 1.0, 0.0,
                 0.0, 0.0, 1.0]
        tx = -fx * baseline if side == 'right' else 0.0
        msg.p = [fx,  0.0,  cx,   tx,
                 0.0,  fx,  cy,  0.0,
                 0.0, 0.0, 1.0,  0.0]
        return msg

    def left_cb(self, img):
        self.left_pub.publish(self.make_msg(img, 'left'))

    def right_cb(self, img):
        self.right_pub.publish(self.make_msg(img, 'right'))


def main():
    rclpy.init()
    node = CameraInfoPublisher()
    node.get_logger().info('Publishing camera_info synced to image timestamps on '
                           '/oak/{left,right}/camera_info_cal')
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
