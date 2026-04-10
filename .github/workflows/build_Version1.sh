#!/bin/bash
set -e

# Source ROS 2 Humble setup
source /opt/ros/humble/setup.bash

# Build the workspace
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release

echo "Build complete"