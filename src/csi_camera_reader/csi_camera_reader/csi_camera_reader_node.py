#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
import cv2
from cv_bridge import CvBridge

def gstreamer_pipeline(
        sensor_id=0,
        capture_width=320, 
        capture_height=240, 
        display_width=160,
        display_height=120,
        framerate=5,
        flip_method=0,
    ):
        return (
            "nvarguscamerasrc sensor_mode=1 sensor-id=%d ! "
            "queue max-size-buffers=1 leaky=downstream ! "
            "video/x-raw(memory:NVMM),width=(int)%d,height=(int)%d,framerate=(fraction)%d/1 ! "
            "nvvidconv flip-method=%d ! "
            "queue ! "
            "video/x-raw,width=(int)%d,height=(int)%d,format=(string)BGRx ! "
            "videoconvert ! "
            "queue ! "
            "video/x-raw,format=(string)BGR ! appsink"
            % (
                sensor_id,
                capture_width,
                capture_height,
                framerate,
                flip_method,
                display_width,
                display_height,
            )
        )

class CsiCameraReaderNode(Node):

    def __init__(self):
        super().__init__('csi_camera_reader_node')
        self.publisher_ = self.create_publisher(Image, 'camera/image_raw', 1)
        timer_period = 1/10 # 10 FPS
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.bridge = CvBridge()



        # GStreamer pipeline for Jetson Nano CSI camera
        self.cap = cv2.VideoCapture(
            gstreamer_pipeline(flip_method=3,framerate=10), cv2.CAP_GSTREAMER)
        if not self.cap.isOpened():
            self.get_logger().error('Failed to open CSI camera.')
        else:
            self.get_logger().info('CSI camera opened successfully.')

    def timer_callback(self):
        ret, frame = self.cap.read()
        if ret:
            msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
            self.publisher_.publish(msg)
            del frame
        else:
            self.get_logger().warn('No frame received from camera.')

    def destroy_node(self):
        if self.cap.isOpened():
            self.cap.release()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = CsiCameraReaderNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()
