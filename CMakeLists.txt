cmake_minimum_required(VERSION 3.16)
project(barrycades CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

set(CMAKE_CXX_FLAGS_RELEASE "-O3 -march=native")

add_library(barrycades_core
  src/state.cpp
  src/annealer.cpp
)
target_include_directories(barrycades_core PUBLIC include)

add_executable(barrycades src/main.cpp)
target_link_libraries(barrycades PRIVATE barrycades_core)
