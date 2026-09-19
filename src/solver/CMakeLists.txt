cmake_minimum_required(VERSION 3.16)
project(barrycades CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

add_library(barrycades_core
  src/state.cpp
  src/annealer.cpp
)
target_include_directories(barrycades_core PUBLIC include)

include(CheckCXXCompilerFlag)
check_cxx_compiler_flag(-march=native HAVE_MARCH_NATIVE)
if(HAVE_MARCH_NATIVE)
  target_compile_options(barrycades_core PUBLIC $<$<CONFIG:Release>:-march=native>)
endif()

add_executable(barrycades src/main.cpp)
target_link_libraries(barrycades PRIVATE barrycades_core)

# `barrycades` is the Python command line, so the solver goes beside it under a
# name of its own. SKBUILD_SCRIPTS_DIR is set only when scikit-build-core drives
# the build, which is how `uv sync` installs the solver into the environment.
set_target_properties(barrycades PROPERTIES OUTPUT_NAME barrycades-solve)

if(DEFINED SKBUILD_SCRIPTS_DIR)
  install(TARGETS barrycades RUNTIME DESTINATION ${SKBUILD_SCRIPTS_DIR})
endif()
