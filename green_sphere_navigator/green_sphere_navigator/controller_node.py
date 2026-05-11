#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan

class ControllerNode(Node):
    def __init__(self):
        super().__init__('controller_node')

        self.declare_parameter('Kp', 0.003)
        self.declare_parameter('error_tolerance', 40.0)
        self.declare_parameter('stop_distance', 0.35)
        self.declare_parameter('search_rot_speed', 0.3)
        self.declare_parameter('linear_speed', 0.12)
        self.declare_parameter('max_angular', 0.5)

        self.error_sub = self.create_subscription(Float64, '/error', self.error_callback, 10)
        self.lidar_sub = self.create_subscription(LaserScan, '/scan', self.scan_callback, 10)
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        self.current_error = 9999.0
        self.front_distance = float('inf')
        self.timer = self.create_timer(0.1, self.control_loop)
        self.get_logger().info('Controller Node started.')

    def error_callback(self, msg):
        self.current_error = msg.data

    def scan_callback(self, msg):
        front = msg.ranges[0:10] + msg.ranges[-10:]
        valid = [r for r in front if msg.range_min < r < msg.range_max]
        self.front_distance = min(valid) if valid else float('inf')

    def control_loop(self):
        cmd = Twist()
        stop_dist = self.get_parameter('stop_distance').value
        tolerance = self.get_parameter('error_tolerance').value
        kp = self.get_parameter('Kp').value
        max_ang = self.get_parameter('max_angular').value
        lin_speed = self.get_parameter('linear_speed').value
        search_rot = self.get_parameter('search_rot_speed').value

        if self.front_distance <= stop_dist:
            self.get_logger().info(f'Stopped at {self.front_distance:.2f}m', once=True)
            self.cmd_pub.publish(cmd)
            return

        if self.current_error == 9999.0:
            cmd.angular.z = search_rot
        else:
            error = self.current_error
            ang = -kp * error
            ang = max(min(ang, max_ang), -max_ang)
            cmd.angular.z = ang
            if abs(error) < tolerance:
                cmd.linear.x = lin_speed

        self.cmd_pub.publish(cmd)

def main(args=None):
    rclpy.init(args=args)
    node = ControllerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
