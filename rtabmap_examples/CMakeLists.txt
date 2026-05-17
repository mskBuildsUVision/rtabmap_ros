cmake_minimum_required(VERSION 3.5)
project(rtabmap_examples)

find_package(ament_cmake REQUIRED)

install(DIRECTORY launch config
   DESTINATION share/${PROJECT_NAME}
)

# Helper scripts (e.g. workarounds like pub_camera_info.py).
# Install into lib/<pkg>/ so they're discoverable via `ros2 run <pkg> <name>`.
install(PROGRAMS
   scripts/pub_camera_info.py
   DESTINATION lib/${PROJECT_NAME}
)

ament_package()