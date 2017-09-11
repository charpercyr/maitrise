
cmake_minimum_required(VERSION 3.7)

project(preload)

add_library(preload MODULE preload.c)

add_executable(run run.c)