cmake_minimum_required(VERSION 2.8.12)
project(cmake_wrapper)

include(conanbuildinfo.cmake)
conan_basic_setup()

# Workaround until https://github.com/conan-io/conan-center-index/issues/1697 is fixed
find_package(absl REQUIRED CONFIG)

add_subdirectory("source_subfolder")
