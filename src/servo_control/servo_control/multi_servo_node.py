import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32
from geometry_msgs.msg import Twist
import serial
import time

class MultiServoNode(Node):
    def __init__(self):
        super().__init__('multi_servo_node')

        # Arduino Mega port
        self.ser = serial.Serial('/dev/ttyUSB0', 57600, timeout=1)
        time.sleep(2)

        # Subscribers (GIỮ NGUYÊN)
        self.create_subscription(Int32, 'neck_cmd', self.cb_neck, 10)
        self.create_subscription(Int32, 'left_arm_cmd', self.cb_left, 10)
        self.create_subscription(Int32, 'right_arm_cmd', self.cb_right, 10)
        self.create_subscription(Int32, 'swing_cmd', self.cb_swing, 10)

        # NEW: subscribe speed
        self.create_subscription(Twist, '/cmd_vel', self.cb_cmd_vel, 10)

        # movement state
        self.robot_moving = False

        self.get_logger().info("Multi Servo Node READY")

    # -------------------------------------------------
    # Callbacks (GIỮ NGUYÊN NHƯ CODE CŨ)
    # -------------------------------------------------

    def cb_neck(self, msg):
        self.send(f"N {msg.data}")

    def cb_left(self, msg):
        self.send(f"L {msg.data}")

    def cb_right(self, msg):
        self.send(f"R {msg.data}")

    def cb_swing(self, msg):
        self.send(f"M {msg.data}")

    # -------------------------------------------------
    # NEW — Auto swing based on robot motion
    # -------------------------------------------------

    def cb_cmd_vel(self, msg: Twist):
        linear = msg.linear.x
        angular = msg.angular.z

        moving = abs(linear) > 0.01 or abs(angular) > 0.01

        if moving and not self.robot_moving:
            self.robot_moving = True
            self.send("M 1")   # turn ON swing
            self.get_logger().info("Robot moving → Swing ON")

        elif not moving and self.robot_moving:
            self.robot_moving = False
            self.send("M 0")   # turn OFF swing
            self.get_logger().info("Robot stopped → Swing OFF")

    # -------------------------------------------------
    # Serial send (GIỮ NGUYÊN "\r")
    # -------------------------------------------------

    def send(self, text):
        cmd = text + "\r"      # Arduino requires CR (ASCII 13)
        self.ser.write(cmd.encode())
        self.get_logger().info(f"Sent: {text}")


def main(args=None):
    rclpy.init(args=args)
    node = MultiServoNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()