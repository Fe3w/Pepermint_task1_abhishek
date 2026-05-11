# Pepermint_task1_abhishek


## 🎥 Task Demonstration
**[Click here to watch the demonstration video](https://drive.google.com/file/d/1aY7igPJU_6GFQV4bKf4B8uDwmZPM0OdH/view)**

---

## Overview
This repository contains a ROS 2 Humble package designed to autonomously navigate a TurtleBot3 towards a green sphere in a Gazebo Classic simulated environment.

The system uses two nodes based on computer vision (OpenCV) and a proportional motion controller, ensuring modular and responsive robot behaviour.

**Key Features**
- Detects a green sphere using HSV colour thresholding
- Computes the sphere's horizontal centroid offset
- Uses a P‑controller to rotate and align the robot
- Moves forward when aligned, stopping at a safe LiDAR distance
- Recovers automatically if the sphere leaves the camera’s field of view

---


The **vision_node** processes the raw camera image, finds the largest green contour and publishes the horizontal pixel error to `/error`. The **controller_node** uses a proportional gain to steer the robot, and the LiDAR data to stop when the sphere is close.

---

### 1. Vision Node (`vision_node.py`)
This node acts as the robot's “eyes”. It subscribes to `/camera/image_raw` and processes the BGR feed to locate the green sphere.

- **Colour Space Conversion** – Converts BGR to HSV to robustly handle Gazebo’s lighting.
- **Thresholding & Morphology** – Applies a green‑hue mask and morphological opening to remove noise.
- **Centroid Calculation** – Finds the largest contour and uses `cv2.moments` to compute the centre of mass `(cx, cy)`.
- **Error Calculation** – Publishes the horizontal pixel error `(cx - image_center_x)` to `/error`.  
  *Positive error = object to the right of centre; negative = to the left.*
- **Out‑of‑Frame Recovery** – If no valid green contour is found, a sentinel value of `9999.0` is published to signal the controller to enter search mode.

HSV thresholds are exposed as ROS 2 parameters and can be tuned at runtime (default: `hue_low=30, hue_high=90, sat_low=30, sat_high=255, val_low=30, val_high=255, min_contour_area=30`).

---

### 2. Controller Node (`controller_node.py`)
This node acts as the “brain”. It subscribes to `/error` and `/scan`.

- **Visual Servoing (P‑Controller)** – Multiplies the horizontal error by a proportional gain (`Kp=0.003`) to produce an angular velocity command.  
  The sign is inverted (`ang = -Kp * error`) so that positive error (object to the right) causes a right turn.
- **Forward Motion** – When `abs(error) < error_tolerance` (default 40 pixels), the robot moves forward at `linear_speed` (0.12 m/s) while continuously correcting heading.
- **LiDAR Stopping** – Reads the front 20° cone of the laser scan. If the minimum valid distance ≤ `stop_distance` (0.35 m), all velocities are set to zero and the robot stops.
- **Search State** – When the sentinel `9999.0` is received, the robot rotates in place at `search_rot_speed` (0.3 rad/s) until the target is reacquired.

All key values are ROS 2 parameters and can be adjusted on the fly.

---

### How would you account for the object going out of frame? How would you recover?
**Sentinel‑based search state**  
If the green sphere leaves the camera’s field of view, the vision node immediately publishes a special error value of `9999.0`. Upon receiving this, the controller node interprets it as “target lost” and automatically enters a **search mode**:
- It stops any forward linear motion.
- It commands a steady angular velocity (default `0.3 rad/s`), causing the robot to rotate in place and scan the environment.
- The moment the sphere reappears and a valid (non‑9999) error is published, the P‑controller seamlessly resumes tracking.

This approach avoids complex state machines while providing robust recovery.

---

### How would you figure out that the robot is close to the obstacle and stop? Is there any other data you can use?
**LiDAR‑based distance measurement**  
The TurtleBot3’s 2D LiDAR (`/scan`) is used to measure the distance to the nearest obstacle in a narrow front cone (0°±10°). When this distance drops below **0.35 m**, the controller overrides all movement commands and stops the robot completely. This method is:
- **Reliable** – independent of lighting, colour, or sphere size.
- **Precise** – gives direct metric distance.

**Other options considered**  
- **Contour area from the camera** – larger contour = closer object. However, area depends on camera resolution, lighting, and the actual object size, making it less robust.
- **Depth camera** – If available, a depth camera could provide pixel‑wise distance. This would be the most accurate vision‑based method, but requires additional hardware and calibration.

In this implementation, the 2D LiDAR was chosen because it is already integrated into the TurtleBot3 and gives consistent results.

---

## Setup and Installation

### Prerequisites
- Ubuntu 22.04
- ROS 2 (Humble)
- Gazebo Classic
- TurtleBot3 ROS2 Setup
- OpenCV and `cv_bridge`

### 1. Workspace Setup
Clone this repository into your ROS 2 workspace source directory or run the commands below:

```bash
# Source ROS Humble environment
source /opt/ros/humble/setup.bash

# Create workspace
mkdir -p ~/green_follower_ws/src
cd ~/green_follower_ws/src

# Clone the repository
git clone https://github.com/Fe3w/Pepermint_task1_abhishek.git green_sphere_navigator

# Install dependencies
cd ~/green_follower_ws
sudo apt update
rosdep update
rosdep install --from-paths src --ignore-src -r -y

# Build the workspace
colcon build --symlink-install
source install/setup.bash
