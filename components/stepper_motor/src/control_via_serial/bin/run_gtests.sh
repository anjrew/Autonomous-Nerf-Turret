cmake -S . -B build
cmake --build build
cd build && ctest --output-on-failure