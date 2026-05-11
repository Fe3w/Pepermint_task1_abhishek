# Pepermint_task1_abhishek


## 🎥 Task Demonstration
**[Click here to watch the demonstration video](https://drive.google.com/file/d/1aY7igPJU_6GFQV4bKf4B8uDwmZPM0OdH/view)**

---

## 📖 Overview
Briefly describe what this project is, what it does, and why you built it. Keep it to a few sentences explaining the main objective.

## ✨ Features
* Highlight the core functionality here.
* Example: Real-time sensor data transmission.
* Example: Custom 3D-printed chassis design.

## 🛠️ Tech Stack & Requirements
List the hardware and software tools used to run this project.
* **Hardware:** (e.g., ESP32, specific sensors, motors)
* **Software:** (e.g., ROS 2, C++, Python, MQTT)

## 🚀 Setup and Installation
Provide step-by-step instructions on how to get the project running locally.

# Source ROS Humble environment
source /opt/ros/humble/setup.bash

# Create workspace
mkdir -p ~/green_follower_ws/src
cd ~/green_follower_ws/src

# Clone the repository
git clone https://github.com/Fe3w/Pepermint_task1_abhishek.git green_sphere_navigator

# Move back to workspace root and install dependencies
cd ~/green_follower_ws
sudo apt update
rosdep update
rosdep install --from-paths src --ignore-src -r -y

# Build and launch
colcon build --symlink-install
source install/setup.bash
export TURTLEBOT3_MODEL=waffle
ros2 launch green_sphere_navigator follow_sphere.launch.py
