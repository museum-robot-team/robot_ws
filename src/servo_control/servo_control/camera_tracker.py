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

        # ROS interfaces
        self.subscription = self.create_subscription(
            Image, '/image_raw', self.image_callback, 10)
        self.publisher = self.create_publisher(Int32, 'neck_cmd', 10)

        # OpenCV converter
        self.bridge = CvBridge()

        # Servo settings
        self.angle = 80.0
        self.min_angle = 65
        self.max_angle = 100

        self.filter_window = []
        self.alpha = 0.35
        self.deadzone = 20

        # Timing
        self.last_time = time.time()
        self.last_face_time = time.time()
        self.last_face_y = None

        # Logging
        self.log_file = open("servo_log.csv", "w", newline="")
        self.csv_writer = csv.writer(self.log_file)
        self.csv_writer.writerow(["timestamp", "servo_angle", "error_y", "fps"])

        # Mediapipe face detection
        self.mp_face = mp.solutions.face_detection
        self.face_detection = self.mp_face.FaceDetection(
            model_selection=0,
            min_detection_confidence=0.8
        )

        self.get_logger().info("Camera Tracker started (65°–100°, stable tracking, fallback after 5s)")

    def image_callback(self, msg):
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_detection.process(rgb)

        h, w, _ = frame.shape
        yc = h // 2
        error_y = 0
        now = time.time()

        # ===================================================
        # 1) FACE FOUND → NORMAL TRACKING
        # ===================================================
        if results.detections:

            # Choose largest face
            best_det = None
            best_area = 0
            for det in results.detections:
                box = det.location_data.relative_bounding_box
                area = box.width * box.height

                if box.height * h < h * 0.15:  # ignore tiny detections
                    continue

                if area > best_area:
                    best_area = area
                    best_det = det

            if best_det is None:
                return

            self.last_face_time = now  # reset timer

            bbox = best_det.location_data.relative_bounding_box
            ymin = int(bbox.ymin * h)
            bh = int(bbox.height * h)
            yf = ymin + bh // 2
            error_y = yf - yc

            # Face consistency (avoid sudden wrong detection)
            if self.last_face_y is not None and abs(yf - self.last_face_y) > h * 0.30:
                return
            self.last_face_y = yf

            # Control logic
            if abs(error_y) > self.deadzone:
                raw_angle = self.angle + error_y / 30.0

                # Moving average filter
                self.filter_window.append(raw_angle)
                if len(self.filter_window) > 5:
                    self.filter_window.pop(0)
                filtered = sum(self.filter_window) / len(self.filter_window)

                # Exponential smoothing
                self.angle = (1 - self.alpha) * self.angle + self.alpha * filtered

            # Clamp
            self.angle = max(self.min_angle, min(self.max_angle, self.angle))

            # Publish
            msg_out = Int32()
            msg_out.data = int(self.angle)
            self.publisher.publish(msg_out)

        # ===================================================
        # 2) NO FACE → After 5s return to 80° smoothly
        # ===================================================
        else:
            if now - self.last_face_time > 5.0:
                target_angle = 80.0
                self.angle += (target_angle - self.angle) * 0.05

                self.angle = max(self.min_angle, min(self.max_angle, self.angle))

                msg_out = Int32()
                msg_out.data = int(self.angle)
                self.publisher.publish(msg_out)

        # ===================================================
        # 3) FPS + LOGGING
        # ===================================================
        fps = 1.0 / (now - self.last_time)
        self.last_time = now

        self.csv_writer.writerow([now, self.angle, error_y, fps])
        self.log_file.flush()

        cv2.putText(frame, f"Angle: {self.angle:.1f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
        cv2.putText(frame, f"FPS: {fps:.1f}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

        cv2.imshow("Face Tracker", frame)
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