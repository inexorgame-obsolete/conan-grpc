cmake_minimum_required(VERSION 3.1.5)
project(test_package)

set(CMAKE_VERBOSE_MAKEFILE TRUE)

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()

if(NOT MSVC)
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11")
else()
  add_definitions(-D_WIN32_WINNT=0x600)
endif()

find_package(protoc CONFIG REQUIRED)

message(STATUS "Using protobuf ${protobuf_VERSION}")

#for target file protoc
set(PROTOS helloworld.proto)

# Proto file
get_filename_component(hw_proto "helloworld.proto" ABSOLUTE)
get_filename_component(hw_proto_path "${hw_proto}" PATH)

include_directories(${CMAKE_CURRENT_BINARY_DIR} ${CMAKE_CURRENT_SOURCE_DIR})


#WHY isnt this working ?
if(protobuf_MODULE_COMPATIBLE)
  protobuf_generate_cpp(PROTO_SRCS PROTO_HDRS ${PROTOS})
else()
  message("protobuf module is incompatible")
endif()
#PROTOBUF_GENERATE_CPP(PROTO_SRCS PROTO_HDRS ${PROTOS})
#generate protobuf stuff
#protobuf_generate_cpp(PROTO_SRCS PROTO_HDRS ${PROTOS})
#generate grpc stuff
#grpc_generate_cpp(GRPC_SRCS GRPC_HDRS ${CMAKE_CURRENT_BINARY_DIR} ${PROTOS})
find_program(_GRPC_CPP_PLUGIN_EXECUTABLE grpc_cpp_plugin)
# Generated sources
set(hw_proto_srcs "${CMAKE_CURRENT_BINARY_DIR}/helloworld.pb.cc")
set(hw_proto_hdrs "${CMAKE_CURRENT_BINARY_DIR}/helloworld.pb.h")
set(hw_grpc_srcs "${CMAKE_CURRENT_BINARY_DIR}/helloworld.grpc.pb.cc")
set(hw_grpc_hdrs "${CMAKE_CURRENT_BINARY_DIR}/helloworld.grpc.pb.h")

set(GEN_SRCS ${hw_proto_srcs} ${hw_proto_hdrs} ${hw_grpc_srcs} ${hw_grpc_hdrs})
add_custom_command(
  OUTPUT ${GEN_SRCS}
  BYPRODUCTS ${GEN_SRCS}
  COMMAND $<TARGET_FILE:protobuf::protoc>
  ARGS --grpc_out "${CMAKE_CURRENT_BINARY_DIR}"
       --cpp_out "${CMAKE_CURRENT_BINARY_DIR}"
        -I "${hw_proto_path}"
        --plugin=protoc-gen-grpc=${_GRPC_CPP_PLUGIN_EXECUTABLE}
        ${PROTOS}
  DEPENDS ${ABS_FIL} $<TARGET_FILE:protobuf::protoc> ${_GRPC_CPP_PLUGIN_EXECUTABLE}
  COMMENT "Running C++ gRPC compiler on ${PROTOS}"
  VERBATIM )

add_custom_target(dummy DEPENDS ${GEN_SRCS})
add_executable(greeter_client dummy.c)
add_dependencies(greeter_client dummy )
