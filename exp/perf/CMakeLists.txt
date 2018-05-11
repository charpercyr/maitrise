cmake_minimum_required(VERSION 3.0)

add_executable(perf perf.cpp)
target_link_libraries(perf dyntrace-fasttp)