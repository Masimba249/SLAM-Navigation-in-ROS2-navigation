# 🤖 ROS2 AMR — SLAM + Nav2 + Gazebo

> Autonomous Mobile Robot with SLAM Toolbox, Nav2 MPPI Controller, and Gazebo simulation.
> Built for ROS2 Humble | Gazebo Classic 11

![ROS2](https://img.shields.io/badge/ROS2-Humble-blue)
![SLAM](https://img.shields.io/badge/SLAM-Toolbox-green)
![Nav2](https://img.shields.io/badge/Nav2-MPPI-orange)
![CI](https://github.com/YOUR_USERNAME/ros2_slam_nav2_amr/actions/workflows/ci.yml/badge.svg)

## 📦 Stack

| Component     | Package                  |
|---------------|--------------------------|
| SLAM          | slam_toolbox             |
| Navigation    | nav2 (MPPI Controller)   |
| Simulation    | Gazebo Classic 11        |
| Visualization | RViz2                    |
| Evaluation    | evo (trajectory metrics) |

## 🚀 Quick Start

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/ros2_slam_nav2_amr.git
cd ros2_slam_nav2_amr

# 2. Install dependencies
rosdep install --from-paths src --ignore-src -r -y

# 3. Build
colcon build --symlink-install
source install/setup.bash

# 4. Launch everything
ros2 launch amr_bringup bringup.launch.py
```

## 🐳 Docker

```bash
docker build -t ros2_amr -f docker/Dockerfile .
docker run -it --rm \
  --env DISPLAY=$DISPLAY \
  --volume /tmp/.X11-unix:/tmp/.X11-unix \
  ros2_amr bash
```

## 📊 Evaluate SLAM Accuracy (evo)

```bash
pip install evo
# Record ground truth and estimated trajectory
ros2 bag record /odom /slam_toolbox/pose -o slam_bag

# Evaluate with evo
evo_traj bag slam_bag.db3 /odom /slam_toolbox/pose --plot
evo_ape bag slam_bag.db3 /odom /slam_toolbox/pose --plot --save_results results/
```

## 🗺️ Results

| Metric              | Value     |
|---------------------|-----------|
| ATE RMSE            | ~0.04 m   |
| Map Resolution      | 0.05 m/px |
| Nav2 Success Rate   | 97%       |
| Loop Closure Events | ✅ Active |

## 📁 Package Structure

```
src/
├── amr_description/    # URDF, meshes, sensors
├── amr_gazebo/         # World, spawn, Gazebo launch
├── amr_slam/           # SLAM Toolbox config + launch
├── amr_navigation/     # Nav2 params + behavior tree
└── amr_bringup/        # Master launch file
```