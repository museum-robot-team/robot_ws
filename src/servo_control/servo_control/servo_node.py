import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32
import serial
import time

class ServoNode(Node):
    def __init__(self):
        super().__init__('servo_node')

        # Serial tới Arduino
        self.ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
        time.sleep(2)  # chờ Arduino reset

        # Nhận góc từ ROS
        self.subscription = self.create_subscription(
            Int32, 'servo_angle_cmd', self.listener_callback, 10)
        self.get_logger().info("Servo Node started, waiting for angle commands...")

    def listener_callback(self, msg):
        angle = int(msg.data)
        command = f"{angle}\n"
        self.ser.write(command.encode('utf-8'))
        self.get_logger().info(f"Sent angle to Arduino: {angle}")

def main(args=None):
    rclpy.init(args=args)
    node = ServoNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
