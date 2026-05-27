#!/usr/bin/env python3
import copy

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CameraInfo, Image


class CameraInfoPublisher(Node):
    def __init__(self):
        super().__init__('camera_info_publisher')
        self.left_pub = self.create_publisher(CameraInfo, '/oak/left/camera_info_cal', 10)
        self.right_pub = self.create_publisher(CameraInfo, '/oak/right/camera_info_cal', 10)
        self.create_subscription(Image, '/oak/left/image_raw', self.left_cb, 10)
        self.create_subscription(Image, '/oak/right/image_raw', self.right_cb, 10)

    def make_msg(self, img, side):
        msg = CameraInfo()
        msg.header = copy.deepcopy(img.header)
        msg.width, msg.height = img.width, img.height
        fx = img.width * 0.8
        cx, cy = img.width / 2.0, img.height / 2.0
        tx = -fx * 0.075 if side == 'right' else 0.0
        msg.distortion_model = 'plumb_bob'
        msg.d = [0.0, 0.0, 0.0, 0.0, 0.0]
        msg.k = [fx, 0.0, cx, 0.0, fx, cy, 0.0, 0.0, 1.0]
        msg.r = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
        msg.p = [fx, 0.0, cx, tx, 0.0, fx, cy, 0.0, 0.0, 0.0, 1.0, 0.0]
        return msg

    def left_cb(self, img):
        self.left_pub.publish(self.make_msg(img, 'left'))

    def right_cb(self, img):
        self.right_pub.publish(self.make_msg(img, 'right'))


rclpy.init()
node = CameraInfoPublisher()
node.get_logger().info('Publishing synced camera_info on /oak/{left,right}/camera_info_cal')
rclpy.spin(node)
