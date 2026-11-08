FROM ros:jazzy-ros-base

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Warsaw
ENV ROS_DISTRO=jazzy
ENV ROS_WS=/ws
ENV RMW_IMPLEMENTATION=rmw_fastrtps_cpp
ENV ROS_DOMAIN_ID=42
# UDP-only Fast DDS profile (see docker/dds/fastdds_udp.xml). Jazzy reads the
# FASTDDS_ name; the FASTRTPS_ name is kept for older tools.
ENV FASTDDS_DEFAULT_PROFILES_FILE=/etc/smx/fastdds_udp.xml
ENV FASTRTPS_DEFAULT_PROFILES_FILE=/etc/smx/fastdds_udp.xml

SHELL ["/bin/bash", "-c"]

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    curl \
    wget \
    usbutils \
    udev \
    minicom \
    picocom \
    python3-pip \
    python3-vcstool \
    python3-rosdep \
    python3-colcon-common-extensions \
    python3-colcon-mixin \
    python3-argcomplete \
    ros-jazzy-ros2-control \
    ros-jazzy-ros2-controllers \
    ros-jazzy-controller-manager \
    ros-jazzy-robot-state-publisher \
    ros-jazzy-ros2controlcli \
    ros-jazzy-xacro \
    && rm -rf /var/lib/apt/lists/*

RUN rosdep init 2>/dev/null || true && rosdep update

WORKDIR ${ROS_WS}
RUN mkdir -p ${ROS_WS}/src

# Import only the Robot PC's DYNAMIXEL dependencies. Operator PC packages
# (MoveIt, RViz, Gazebo) are intentionally excluded from this image.
COPY ros2_robot.repos /tmp/ros2_robot.repos
RUN vcs import --input /tmp/ros2_robot.repos ${ROS_WS}/src

# Project-owned packages only. Upstream ROBOTIS sources stay separate.
COPY ros2_ws/src/smartmanipulator_x ${ROS_WS}/src/smartmanipulator_x

RUN source /opt/ros/${ROS_DISTRO}/setup.bash && \
    rosdep install \
            --from-paths \
                ${ROS_WS}/src/robotis/DynamixelSDK/ros/dynamixel_sdk \
                ${ROS_WS}/src/robotis/dynamixel_interfaces \
                ${ROS_WS}/src/robotis/dynamixel_hardware_interface \
                ${ROS_WS}/src/smartmanipulator_x \
      --ignore-src \
      --rosdistro ${ROS_DISTRO} \
      -r -y

RUN source /opt/ros/${ROS_DISTRO}/setup.bash && \
    colcon build \
            --base-paths \
                ${ROS_WS}/src/robotis/DynamixelSDK/ros/dynamixel_sdk \
                ${ROS_WS}/src/robotis/dynamixel_interfaces \
                ${ROS_WS}/src/robotis/dynamixel_hardware_interface \
                ${ROS_WS}/src/smartmanipulator_x \
      --symlink-install \
      --cmake-args -DCMAKE_BUILD_TYPE=RelWithDebInfo

COPY docker/dds/fastdds_udp.xml /etc/smx/fastdds_udp.xml
COPY tools/diagnostics /opt/smx/diagnostics
# sed: tolerate CRLF checkouts on Windows hosts.
RUN find /opt/smx/diagnostics -name '*.sh' -exec sed -i 's/\r$//' {} + -exec chmod +x {} +

COPY docker/entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

RUN echo 'source /opt/ros/${ROS_DISTRO}/setup.bash' >> /root/.bashrc && \
    echo 'source ${ROS_WS}/install/setup.bash' >> /root/.bashrc && \
    echo 'export PATH=/opt/smx/diagnostics:${PATH}' >> /root/.bashrc
ENV PATH=/opt/smx/diagnostics:${PATH}

ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
