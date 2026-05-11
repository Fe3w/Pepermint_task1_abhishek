# Green Sphere Tracker – ROS 2 Package

This ROS 2 package enables a **TurtleBot3 (Waffle)** in a **Gazebo** simulation to autonomously detect and track a **green spherical target** using **computer vision (OpenCV)** and a **proportional motion controller**. The system is divided into two modular nodes:

- **Vision Node** – processes raw camera images to extract the target’s horizontal error.
- **Controller Node** – uses the error signal and LiDAR data to generate velocity commands.

---

## 🏗️ System Architecture

### 1. Vision Perception (`vision_node.py`)

The vision node subscribes to the raw camera feed (`/image_raw`) and performs the following steps:

| Step | Description |
|------|-------------|
| **Color conversion** | Converts the BGR image to the **HSV** colour space to make green detection robust against lighting variations. |
| **Thresholding** | Applies a binary mask using tunable HSV ranges (default: hue 30–90, saturation 30–255, value 30–255). |
| **Morphological opening** | Removes small false positives (noise) using a 5×5 kernel. |
| **Contour detection** | Finds external contours and selects the **largest** one that exceeds a minimum area threshold. |
| **Centroid calculation** | Computes the centre of mass `(cx, cy)` of the largest contour. |
| **Error publication** | Publishes the **horizontal pixel error** `(cx – image_width/2)` on the `/error` topic as a `Float64`. |
| **Loss of target handling** | If no valid contour is found, the node publishes a **sentinel value** `9999.0`. |

The node can also display a real‑time debug window (optional) that draws the detected centroid, area, and the mask.

#### Key Parameters (Configurable via ROS 2 parameters)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `hue_low` / `hue_high` | 30 / 90 | Lower/upper hue bounds for the green mask. |
| `sat_low` / `sat_high` | 30 / 255 | Saturation bounds. |
| `val_low` / `val_high` | 30 / 255 | Value (brightness) bounds. |
| `min_contour_area` | 30 | Minimum contour area (pixels) to ignore noise. |
| `show_debug_window` | True | Enable/disable the OpenCV debug display. |

---

### 2. Kinematic Controller (`controller_node.py`)

The controller node subscribes to **`/error`** (from the vision node) and **`/scan`** (LiDAR), and publishes **`/cmd_vel`** (`Twist`) messages. Its logic is:

- **Target Search Mode**  
  If the received error equals `9999.0` (target not visible), the robot **rotates in place** at a configurable angular speed (`search_rot_speed`, default 0.5 rad/s). This allows the robot to scan the environment until the green sphere re‑enters the camera field of view.

- **Visual Servoing (P‑controller)**  
  When a valid error is received, the angular velocity is calculated as:  

  ![equation](https://latex.codecogs.com/svg.image?%5Comega_z=-K_p%5Ccdot%5Ctext%7Berror%7D)  
  where `K_p` is the proportional gain (default 0.003). The angular command is clamped to `[-max_angular, max_angular]`.  
  → This turns the robot to **align the camera centre with the target**.

- **Forward Motion**  
  If the **absolute horizontal error** is less than `error_tolerance` (default 40 pixels), the robot **drives straight** with a constant linear velocity (`linear_speed`, default 0.12 m/s) while still applying angular corrections.

- **Collision Avoidance**  
  The node reads the LiDAR ranges within a frontal 20° cone (indices 0–9 and 350–359). If the **minimum valid distance** drops below `stop_distance` (default 0.5 m), all velocity commands are **set to zero** to avoid collision. This is the primary stopping mechanism.

#### Key Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `Kp` | 0.003 | Proportional gain for angular control. |
| `error_tolerance` | 40.0 | Pixel‑error threshold below which the robot moves forward. |
| `stop_distance` | 0.5 | Minimum forward LiDAR distance (m) before stopping. |
| `search_rot_speed` | 0.5 | Angular speed (rad/s) during target‑lost search. |
| `linear_speed` | 0.12 | Forward speed (m/s) when aligned. |
| `max_angular` | 0.5 | Maximum allowed angular velocity (rad/s). |

---

## 📝 Task Questions & Answers

### 🟢 Q: How would you account for the object going out of frame? How would you recover?

**A:** The system uses a **state‑driven recovery mechanism** based on a sentinel value.  

- The **vision node** constantly checks for a valid contour. If none is found (or the target area is too small), it immediately publishes the special error value **`9999.0`**.  
- The **controller node** interprets `9999.0` as *“target lost”* and switches from **tracking mode** to **search mode**. In search mode it sets linear speed to **zero** and commands a constant angular velocity (`search_rot_speed`).  
- This forces the robot to **rotate in place**, systematically scanning its surroundings. As soon as the green sphere re‑appears in the camera frame, the vision node resumes publishing a real error, and the P‑controller seamlessly takes over again.

### 🔴 Q: How would you figure out that the robot is close to the obstacle and stop? Is there any other data you can use?

**A:** The **primary method** uses the robot’s onboard **2D LiDAR** (`/scan` topic).  

- The controller examines the laser ranges from a **20° forward cone** (0° ± 10°).  
- If the **smallest valid distance** inside this cone falls below the configurable `stop_distance` (0.5 m), the node overrides all other motion commands and publishes a **zero‑velocity twist**, safely halting the robot.

**Alternative data sources considered:**

| Source | How it works | Pros / Cons |
|--------|--------------|--------------|
| **Contour area (OpenCV)** | The green sphere’s bounding‑box area increases as the robot gets closer. A simple distance‑proportional threshold could be used. | ✔ Lightweight, no extra sensor.<br>✘ Highly heuristic; sensitive to lighting, partial occlusion, and requires prior knowledge of target size. |
| **RGB‑D (depth) camera** | If the robot carried an RGB‑D sensor (e.g., Intel RealSense), the depth image would give a **direct metric distance** for every green pixel. | ✔ Robust distance measurement, independent of LiDAR.<br>✘ Requires additional hardware and processing. |

---

## ⚙️ Setup and Installation

### Prerequisites
- **Ubuntu 22.04** (ROS 2 Humble recommended)
- **ROS 2 Humble** desktop‑full installation
- **Gazebo Classic**
- **TurtleBot3** ROS 2 packages (`turtlebot3_gazebo`)
- Python libraries: `opencv-python`, `cv_bridge`, `numpy`

### Workspace Compilation

```bash
# Source ROS 2
source /opt/ros/humble/setup.bash

# Create workspace and clone
mkdir -p ~/green_follower_ws/src
cd ~/green_follower_ws/src
git clone <your-repo-url> green_sphere_navigator

# Install dependencies
cd ~/green_follower_ws
sudo apt update
rosdep update
rosdep install --from-paths src --ignore-src -r -y

# Build
colcon build --symlink-install
source install/setup.bash

# Set TurtleBot3 model (Waffle has both camera and LiDAR)
export TURTLEBOT3_MODEL=waffle
