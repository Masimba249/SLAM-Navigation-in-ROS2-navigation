#!/bin/bash
set -e

# Source ROS 2 Humble setup
source /opt/ros/humble/setup.bash

# Export ROS domain ID
export ROS_DOMAIN_ID=0

# Setup colcon
export COLCON_DEFAULTS_DIR=~/.colcon

echo "ROS 2 Humble environment setup complete"