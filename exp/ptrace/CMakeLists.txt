cmake_minimum_required(VERSION 3.9)

project(ptrace)

add_library(inject MODULE inject.c)

target_link_libraries(inject elf)

add_executable(traced traced.c)