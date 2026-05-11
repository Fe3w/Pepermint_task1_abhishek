# Pepermint_task1_abhishek


## 🎥 Task Demonstration
**[Click here to watch the demonstration video]([https://drive.google.com/file/d/1aY7igPJU_6GFQV4bKf4B8uDwmZPM0OdH/view](https://github.com/user-attachments/assets/0037292b-5833-48bb-ab2b-4b447e59ce83))**



https://github.com/user-attachments/assets/0037292b-5833-48bb-ab2b-4b447e59ce83

---

## 📌 Overview

This repository contains a ROS 2 package designed to fulfill the requirements of autonomous target-tracking using a TurtleBot3 in a Gazebo simulated environment. The system utilizes computer vision (OpenCV) to detect a specific green spherical target and a proportional motion controller to navigate the robot towards it. 

The architecture is divided into two highly modular nodes: a **Vision Node** for image processing and state estimation, and a **Controller Node** for executing kinematic commands based on sensory feedback.

---

## 🏗️ System Architecture

### 1. Vision Perception (`vision_node.py`)
This node is responsible for processing raw camera feeds to isolate the target and compute the necessary trajectory corrections.

* **Image Acquisition:** Subscribes to the `/camera/image_raw` topic.
* **Color Space Conversion & Thresholding:** Converts incoming BGR images to the HSV color space to mitigate lighting variances in the Gazebo environment. A dynamic mask isolates the green hue.
* **Morphological Operations:** Applies an opening morphological transformation to eliminate high-frequency noise and false positives.
* **Centroid & Error Computation:** Extracts the largest valid contour and calculates its spatial moments to find the center of mass $(c_x, c_y)$. It then computes the horizontal pixel error relative to the image's center and publishes this value to the `/error` topic.
* **Loss of Target Handling:** If no valid contour is detected, the node publishes a predefined sentinel value (`9999.0`) to signal a tracking failure to the controller.

### 2. Kinematic Controller (`controller_node.py`)
This node processes the error signals and environmental data to calculate and publish velocity commands.

* **Visual Servoing (P-Controller):** Subscribes to the `/error` topic. The angular velocity is governed by a proportional controller ($\omega_z = -K_p \times \text{error}$), aligning the robot with the target. 
* **Forward Kinematics:** When the absolute horizontal error falls below a defined tolerance threshold, the robot initiates a constant linear velocity toward the target while maintaining heading corrections.
* **Collision Avoidance:** Subscribes to the `/scan` topic. It monitors the LiDAR data within a frontal 20° cone. If the minimum distance reading breaches the safety threshold, all velocity commands are nullified.

---

## 📝 Formal Task Responses

**Q: How would you account for the object going out of frame? How would you recover?**

**A:** The system employs a state-driven recovery mechanism utilizing a sentinel flag. If the target object leaves the camera's field of view, the `vision_node` instantly fails to find a valid contour meeting the minimum area requirements. It immediately publishes a sentinel error value of `9999.0`. 

Upon receiving this specific value, the `controller_node` transitions from "tracking mode" to "search mode." It halts all linear progression ($v_x = 0$) and commands a constant angular velocity (defaulting to $0.5$ rad/s). This forces the robot to rotate in place, systematically scanning its environment until the green sphere re-enters the frame, at which point standard P-controller tracking seamlessly resumes.

**Q: How would you figure out that the robot is close to the obstacle and stop? Is there any other data you can use?**

**A:** The primary method for obstacle proximity detection in this package relies on the robot's onboard 2D LiDAR. The `controller_node` processes the `/scan` data, isolating an array of laser ranges from the front of the robot (0° ± 10°). If the minimum valid distance within this cone drops below the configurable `stop_distance` parameter (set to 0.5 meters), the node overrides the tracking logic and commands a zero-velocity twist message, safely stopping the robot.

**Alternative Data Sources Considered:**
* **Contour Area Calculation:** The area of the target's bounding box or contour (calculated via OpenCV) increases inversely with distance. While computationally inexpensive, this is a highly heuristic approach vulnerable to lighting changes, partial occlusions, and requires prior knowledge of the object's true dimensions.
* **RGB-D (Depth) Camera:** If equipped, a depth sensor (like an Intel RealSense) provides direct metric distances for every pixel. This would allow the system to map the exact distance of the contour's centroid, offering a highly robust vision-only stopping criteria without relying on a separate 2D LiDAR plane.

---

## ⚙️ Setup and Installation

### Prerequisites
* Ubuntu 22.04
* ROS 2 (Humble)
* Gazebo Classic
* TurtleBot3 ROS 2 Packages
* `cv_bridge` and `OpenCV` Python libraries

### Workspace Compilation

Execute the following commands to clone and build the package within a ROS 2 workspace:

```bash
# Source ROS Humble environment
source /opt/ros/humble/setup.bash

# Create and navigate to the workspace
mkdir -p ~/green_follower_ws/src
cd ~/green_follower_ws/src

# Clone the repository
git clone [https://github.com/Fe3w/Pepermint_task1_abhishek.git](https://github.com/Fe3w/Pepermint_task1_abhishek.git) green_sphere_navigator

# Move to workspace root and install dependencies
cd ~/green_follower_ws
sudo apt update
rosdep update
rosdep install --from-paths src --ignore-src -r -y

# Build the package
colcon build --symlink-install
source install/setup.bash

# Set TurtleBot3 model variable (Waffle model provides the necessary camera/LiDAR)
export TURTLEBOT3_MODEL=waffle
