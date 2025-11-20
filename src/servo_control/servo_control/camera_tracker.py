import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Int32
import cv2
from cv_bridge import CvBridge
import mediapipe as mp
import time
import csv
import os

class CameraTracker(Node):
    def __init__(self):
        super().__init__('camera_tracker')

        # Subscribers & Publishers
        self.subscription = self.create_subscription(
            Image, '/image_raw', self.image_callback, 10)
        self.publisher = self.create_publisher(Int32, 'servo_angle_cmd', 10)

        # OpenCV bridge
        self.bridge = CvBridge()

        # Servo control
        self.angle = 80.0
        self.filter_window = []
        self.alpha = 0.2  # smoothing factor
        self.deadzone = 20

        # Giới hạn tilt
        self.min_angle = 65
        self.max_angle = 100

        # FPS tracking
        self.last_time = time.time()

        # Logging setup
        self.log_path = "servo_log.csv"
        self.log_file = open(self.log_path, "w", newline="")
        self.csv_writer = csv.writer(self.log_file)
        self.csv_writer.writerow(["timestamp", "servo_angle", "error_y", "fps"])

        # MediaPipe Face Detection
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=0, min_detection_confidence=0.8)

        self.get_logger().info("Camera Tracker started (Face Tracking Tilt 65°–100°)")

    def image_callback(self, msg):
        # Convert ROS Image to OpenCV
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

        # Image preprocessing (optional)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_detection.process(rgb)

        h, w, _ = frame.shape
        yc = h // 2
        error_y = 0

        if results.detections:
            for detection in results.detections:
                bboxC = detection.location_data.relative_bounding_box
                ymin = int(bboxC.ymin * h)
                bh = int(bboxC.height * h)
                yf = ymin + bh // 2
                error_y = yf - yc

                if abs(error_y) > self.deadzone:
                    raw_angle = self.angle + error_y / 50.0
                    self.filter_window.append(raw_angle)
                    if len(self.filter_window) > 5:
                        self.filter_window.pop(0)
                    avg_angle = sum(self.filter_window) / len(self.filter_window)
                    self.angle = (1 - self.alpha) * self.angle + self.alpha * avg_angle

                # Giới hạn góc tilt [65, 100]
                self.angle = max(self.min_angle, min(self.max_angle, self.angle))

                # Publish
                msg_out = Int32()
                msg_out.data = int(self.angle)
                self.publisher.publish(msg_out)

                cv2.rectangle(frame,
                              (int(bboxC.xmin * w), int(bboxC.ymin * h)),
                              (int((bboxC.xmin + bboxC.width) * w), int((bboxC.ymin + bboxC.height) * h)),
                              (0, 255, 0), 2)
                cv2.line(frame, (0, yc), (w, yc), (0, 0, 255), 2)

        # FPS
        now = time.time()
        fps = 1.0 / (now - self.last_time)
        self.last_time = now

        # Log
        self.csv_writer.writerow([now, self.angle, error_y, fps])
        self.log_file.flush()

        cv2.putText(frame, f"Angle: {self.angle:.1f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
        cv2.putText(frame, f"FPS: {fps:.1f}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

        cv2.imshow('Face Tracker', frame)
        cv2.waitKey(1)

    def destroy_node(self):
        self.log_file.close()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = CameraTracker()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
