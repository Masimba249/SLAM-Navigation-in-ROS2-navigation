#!/bin/bash
set -e

# Source ROS 2 Humble setup
source /opt/ros/humble/setup.bash

# Source the built workspace
source install/setup.bash

# Run tests
colcon test --packages-select amr_description amr_slam amr_navigation
colcon test-result --verbose

echo "Tests complete"