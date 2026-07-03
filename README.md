# 🤖 ROS2 AMR — SLAM + Nav2 + Gazebo

> Autonomous Mobile Robot with SLAM Toolbox, Nav2 MPPI Controller, autonomous
> frontier exploration, and Gazebo simulation.
> Built for ROS2 Humble | Gazebo Harmonic

![ROS2](https://img.shields.io/badge/ROS2-Humble-blue)
![SLAM](https://img.shields.io/badge/SLAM-Toolbox-green)
![Nav2](https://img.shields.io/badge/Nav2-MPPI-orange)
![Gazebo](https://img.shields.io/badge/Gazebo-Harmonic-red)
![CI](https://github.com/YOUR_USERNAME/ros2_slam_nav2_amr/actions/workflows/ci.yml/badge.svg)

## 📦 Stack

| Component            | Package                     |
|-----------------------|-----------------------------|
| SLAM                  | slam_toolbox                |
| Navigation            | nav2 (MPPI Controller)      |
| Autonomous exploration| amr_explore (frontier-based)|
| Simulation            | Gazebo Harmonic (gz-sim)    |
| Visualization         | RViz2                       |
| Evaluation            | evo (trajectory metrics)    |

> Gazebo Classic is not used here — Classic and Harmonic can't be installed
> side by side, so if your machine already has a different Gazebo Harmonic
> variant, adjust the `ros-gzharmonic-*` package names in the install step
> below to match (see [Simulator variants](#-simulator-variants)).

## 🚀 Quick Start

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/ros2_slam_nav2_amr.git
cd ros2_slam_nav2_amr

# 2. Install dependencies
sudo apt install ros-humble-xacro ros-humble-joint-state-publisher \
  ros-humble-ros-gzharmonic-sim ros-humble-ros-gzharmonic-bridge \
  ros-humble-slam-toolbox ros-humble-nav2-bringup

# 3. Build
colcon build --symlink-install
source install/setup.bash        # fish shell: use `bass source install/setup.bash`

# 4. Launch everything — Gazebo, SLAM, Nav2, autonomous exploration, RViz
ros2 launch amr_bringup bringup.launch.py
```

The robot spawns, `slam_toolbox` starts building the map, and once Nav2 is up
(a few seconds in) `amr_explore` starts driving the robot to unexplored map
frontiers on its own — no manual teleop needed. Watch it happen live in RViz
or the Gazebo GUI. To drive manually instead, launch with `explore:=false`
and publish `geometry_msgs/Twist` on `/cmd_vel` yourself (e.g.
`ros2 run teleop_twist_keyboard teleop_twist_keyboard`).

### 🌐 Simulator variants

`ros-humble-ros-gzharmonic-sim`/`-bridge` are the Gazebo-Harmonic-targeted
builds of `ros_gz_sim`/`ros_gz_bridge` — use these if Harmonic (`gz-sim8`) is
already on your machine (e.g. installed for another project). If your system
has no other Gazebo installed, the plain `ros-humble-ros-gz-sim` /
`ros-humble-ros-gz-bridge` packages (which target Gazebo Fortress) work too;
either way the ROS package names used in the launch files
(`ros_gz_sim`, `ros_gz_bridge`) stay the same.

## 🐳 Docker

```bash
docker build -t ros2_amr -f docker/Dockerfile .
docker run -it --rm \
  --env DISPLAY=$DISPLAY \
  --volume /tmp/.X11-unix:/tmp/.X11-unix \
  ros2_amr bash
```

> `docker/Dockerfile` still installs Gazebo Classic packages left over from
> before the Harmonic port — it needs the same dependency swap as the Quick
> Start step above before the image will build/run correctly.

## 📊 Evaluate SLAM Accuracy (evo)

```bash
pip install evo
# Record ground truth and estimated trajectory
ros2 bag record /odom /pose -o slam_bag

# Evaluate with evo
evo_traj bag slam_bag.db3 /odom /pose --plot
evo_ape bag slam_bag.db3 /odom /pose --plot --save_results results/
```

## ✅ Status

Verified end-to-end on ROS 2 Humble + Gazebo Harmonic:
- `colcon build` succeeds across all 6 packages
- Gazebo spawns the robot and simulates the diff-drive base, LiDAR, and IMU
- `slam_toolbox` builds an occupancy map live from the simulated scan
- Nav2 (MPPI controller) plans and drives to goals
- `amr_explore` autonomously drives the robot to unexplored frontiers until
  the map is fully covered, with no manual input

No trajectory-accuracy numbers (ATE/RPE) have been benchmarked yet — run the
`evo` commands above against your own `ros2 bag` recording to get real
figures rather than relying on placeholder metrics.

## 📁 Package Structure

```
src/
├── amr_description/    # URDF, meshes, sensors
├── amr_gazebo/         # Gazebo Harmonic world, bridge config, sim launch
├── amr_slam/           # SLAM Toolbox config + launch
├── amr_navigation/     # Nav2 params + behavior tree
├── amr_explore/        # Frontier-based autonomous exploration node
└── amr_bringup/        # Master launch file
```