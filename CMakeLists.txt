cmake_minimum_required(VERSION 2.8.12)
project(cmake_wrapper)

include(conanbuildinfo.cmake)
conan_basic_setup()

if(NOT Protobuf_PROTOC_EXECUTABLE)
    message(FATAL_ERROR "Expected Conan to provide: 'Protobuf_PROTOC_EXECUTABLE'")
endif()
# GRPC will find the wrong protoc when cross building.
# Override it here.
set(_gRPC_PROTOBUF_PROTOC_EXECUTABLE ${Protobuf_PROTOC_EXECUTABLE})

add_subdirectory("source_subfolder")
