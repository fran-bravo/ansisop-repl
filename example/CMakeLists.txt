cmake_minimum_required(VERSION 3.2)
project(example_ansisop)

set(CMAKE_C_STANDARD 99)

set(SOURCE_FILES main.c)
add_executable(example_ansisop ${SOURCE_FILES})
target_link_libraries(example_ansisop commons)