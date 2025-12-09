import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32


class ArmAnimation(Node):
    def __init__(self):
        super().__init__('arm_animation')

        self.pub_swing = self.create_publisher(Int32, 'swing_cmd', 10)

        # Toggle M0 / M1 mỗi 5 giây
        self.state = False
        

        self.get_logger().info("ArmAnimation node started")

    def switch(self):
        self.state = not self.state
        msg = Int32()
        msg.data = 1 if self.state else 0
        self.pub_swing.publish(msg)
        self.get_logger().info(f"Swing mode: {msg.data}")


def main(args=None):
    rclpy.init(args=args)
    node = ArmAnimation()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()