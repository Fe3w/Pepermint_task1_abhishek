#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Float64
from cv_bridge import CvBridge
import cv2
import numpy as np

class VisionNode(Node):
    def __init__(self):
        super().__init__('vision_node')

        self.declare_parameter('hue_low', 30)
        self.declare_parameter('hue_high', 90)
        self.declare_parameter('sat_low', 30)
        self.declare_parameter('sat_high', 255)
        self.declare_parameter('val_low', 30)
        self.declare_parameter('val_high', 255)
        self.declare_parameter('min_contour_area', 30)
        self.declare_parameter('show_debug_window', True)

        self.subscription = self.create_subscription(
            Image,
            'image_raw',
            self.image_callback,
            10)

        self.error_pub = self.create_publisher(Float64, '/error', 10)
        self.bridge = CvBridge()
        self.get_logger().info('Vision Node started.')

    def image_callback(self, msg):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().error(f'cv_bridge error: {e}', once=True)
            return

        height, width, _ = cv_image.shape
        hsv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)

        lower = np.array([
            self.get_parameter('hue_low').value,
            self.get_parameter('sat_low').value,
            self.get_parameter('val_low').value])
        upper = np.array([
            self.get_parameter('hue_high').value,
            self.get_parameter('sat_high').value,
            self.get_parameter('val_high').value])
        min_area = self.get_parameter('min_contour_area').value
        debug = self.get_parameter('show_debug_window').value

        mask = cv2.inRange(hsv, lower, upper)
        kernel = np.ones((5,5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        error_msg = Float64()
        if contours:
            largest = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest)
            if area >= min_area:
                M = cv2.moments(largest)
                if M['m00'] > 0:
                    cx = int(M['m10'] / M['m00'])
                    cy = int(M['m01'] / M['m00'])

                    if debug:
                        cv2.circle(cv_image, (cx, cy), 10, (0, 0, 255), -1)
                        cv2.putText(cv_image, f'Area:{area:.0f}', (cx, cy-15),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)

                    error_value = cx - width / 2.0
                    error_msg.data = float(error_value)
                    self.error_pub.publish(error_msg)
                    return
        error_msg.data = 9999.0
        self.error_pub.publish(error_msg)

        if debug:
            cv2.imshow("Vision Debug", np.hstack((cv_image, cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR))))
            cv2.waitKey(1)

def main(args=None):
    rclpy.init(args=args)
    node = VisionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        cv2.destroyAllWindows()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
