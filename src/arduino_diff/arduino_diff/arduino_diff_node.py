import rclpy
from rclpy.node import Node
import serial
import math
import time

from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from tf_transformations import quaternion_from_euler
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped


class ArduinoDiffDrive(Node):
    def __init__(self):
        super().__init__("arduino_diff_node")

        # ---- SERIAL ----
        self.ser = serial.Serial('/dev/ttyUSB0', 57600, timeout=0.1)
        time.sleep(2)

        # ---- ROBOT PARAMS ----
        self.wheel_radius = 0.0775
        self.wheel_base = 0.50
        self.encoder_cpr = 12 * 4
        self.gear_ratio = 19.2
        self.ticks_per_rev = self.encoder_cpr * self.gear_ratio

        # ---- STATE ----
        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0

        self.prev_left = 0
        self.prev_right = 0
        self.first_read = True

        # ---- ROS INTERFACE ----
        self.sub_cmd = self.create_subscription(
            Twist, "/cmd_vel", self.cmd_callback, 10
        )

        self.pub_odom = self.create_publisher(Odometry, "/odom", 10)
        self.tf_broadcaster = TransformBroadcaster(self)

        self.create_timer(0.02, self.update_odom)  # 50 Hz

    # -------------------------
    # SEND CMD TO ARDUINO
    # -------------------------
    def cmd_callback(self, msg: Twist):
        v = msg.linear.x
        w = msg.angular.z

        v_l = v - w * self.wheel_base / 2
        v_r = v + w * self.wheel_base / 2

        ticks_l = int(v_l / (2 * math.pi * self.wheel_radius) * self.ticks_per_rev * 0.02)
        ticks_r = int(v_r / (2 * math.pi * self.wheel_radius) * self.ticks_per_rev * 0.02)

        cmd = f"m {ticks_l} {ticks_r}\r"
        self.ser.write(cmd.encode())

    # -------------------------
    # READ ENCODER + ODOM
    # -------------------------
    def update_odom(self):
        self.ser.write(b"e\r")

        try:
            line = self.ser.readline().decode().strip()
            if " " not in line:
                return

            left, right = line.split()
            left = int(left)
            right = int(right)
        except:
            return

        if self.first_read:
            self.prev_left = left
            self.prev_right = right
            self.first_read = False
            return

        dL = left - self.prev_left
        dR = right - self.prev_right
        self.prev_left = left
        self.prev_right = right

        dist_L = (dL / self.ticks_per_rev) * (2 * math.pi * self.wheel_radius)
        dist_R = (dR / self.ticks_per_rev) * (2 * math.pi * self.wheel_radius)

        dist = (dist_R + dist_L) / 2.0
        dtheta = (dist_R - dist_L) / self.wheel_base

        self.yaw += dtheta
        self.x += dist * math.cos(self.yaw)
        self.y += dist * math.sin(self.yaw)

        # ---- TF ----
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = "odom"
        t.child_frame_id = "base_link"
        t.transform.translation.x = self.x
        t.transform.translation.y = self.y
        t.transform.translation.z = 0.0

        q = quaternion_from_euler(0, 0, self.yaw)
        t.transform.rotation.x = q[0]
        t.transform.rotation.y = q[1]
        t.transform.rotation.z = q[2]
        t.transform.rotation.w = q[3]

        self.tf_broadcaster.sendTransform(t)

        # ---- ODOM ----
        od = Odometry()
        od.header.stamp = t.header.stamp
        od.header.frame_id = "odom"
        od.child_frame_id = "base_link"

        od.pose.pose.position.x = self.x
        od.pose.pose.position.y = self.y
        od.pose.pose.position.z = 0.0
        od.pose.pose.orientation.x = q[0]
        od.pose.pose.orientation.y = q[1]
        od.pose.pose.orientation.z = q[2]
        od.pose.pose.orientation.w = q[3]

        self.pub_odom.publish(od)


def main(args=None):
    rclpy.init(args=args)
    node = ArduinoDiffDrive()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()