#!/bin/bash

mkdir -p build
cd build
cmake .. -DCMAKE_CXX_FLAGS=-L/opt/dyntrace/lib -DCMAKE_BUILD_TYPE=Release
make