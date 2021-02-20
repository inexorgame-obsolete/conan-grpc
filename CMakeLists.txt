cmake_minimum_required(VERSION 2.8.12)
project(cmake_wrapper)

# Need to find protoc before conan setup to make sure we get the correct
# one when cross compiling.
find_program(_gRPC_PROTOBUF_PROTOC_EXECUTABLE protoc)

include(conanbuildinfo.cmake)
conan_basic_setup()

add_subdirectory("source_subfolder")
