FROM ros:humble-ros-base-jammy

ENV DEBIAN_FRONTEND=noninteractive
SHELL ["/bin/bash", "-c"]

RUN apt-get update && apt-get install -y \
    ros-humble-slam-toolbox \
    ros-humble-nav2-bringup \
    ros-humble-gazebo-ros-pkgs \
    ros-humble-robot-state-publisher \
    ros-humble-rviz2 \
    python3-colcon-common-extensions \
    python3-rosdep \
    git wget curl \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /ros2_ws
COPY . /ros2_ws/

RUN source /opt/ros/humble/setup.bash \
    && rosdep update \
    && rosdep install --from-paths src --ignore-src -r -y \
    && colcon build --symlink-install

RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
RUN echo "source /ros2_ws/install/setup.bash" >> ~/.bashrc

CMD ["bash"]