cmake_minimum_required(VERSION 3.1)
project(test_package)

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()

if(WIN32)
  add_definitions(-D_WIN32_WINNT=0x600)
endif()
set(CMAKE_CXX_STANDARD 11)

# Find Protobuf installation
set(protobuf_MODULE_COMPATIBLE TRUE)
find_package(Protobuf CONFIG REQUIRED)
message(STATUS "Using protobuf ${protobuf_VERSION}")

set(CMAKE_VERBOSE_MAKEFILE ON)

# Find gRPC installation
find_package(gRPC CONFIG REQUIRED)
message(STATUS "Using gRPC ${gRPC_VERSION}")

function(protobuf_generate_grpc_cpp SRCS HDRS)
    if(NOT ARGN)
        message(SEND_ERROR "Error: protobuf_generate_grpc_cpp() called without any proto files")
        return()
    endif()

    if (PROTOBUF_GENERATE_CPP_APPEND_PATH) # This variable is common for all types of output.
        # Create an include path for each file specified
        foreach(FIL ${ARGN})
            get_filename_component(ABS_FIL ${FIL} ABSOLUTE)
            get_filename_component(ABS_PATH ${ABS_FIL} PATH)
            list(FIND _protobuf_include_path ${ABS_PATH} _contains_already)
            if(${_contains_already} EQUAL -1)
                list(APPEND _protobuf_include_path -I${ABS_PATH})
            endif()
        endforeach()
    else()
        set(_protobuf_include_path -I${CMAKE_CURRENT_SOURCE_DIR})
    endif()

    if (DEFINED PROTOBUF_IMPORT_DIRS)
        foreach(DIR ${Protobuf_IMPORT_DIRS})
            get_filename_component(ABS_PATH ${DIR} ABSOLUTE)
            list(FIND _protobuf_include_path ${ABS_PATH} _contains_already)
            if(${_contains_already} EQUAL -1)
                list(APPEND _protobuf_include_path -I${ABS_PATH})
            endif()
        endforeach()
    endif()

    find_program(GRPC_CPP_PLUGIN grpc_cpp_plugin) # Get full path to plugin
    if (NOT GRPC_CPP_PLUGIN)
        message(SEND_ERROR "Error: grpc_cpp_plugin is required")
        return()
    endif()

    set(${SRCS})
    set(${HDRS})
    foreach(FIL ${ARGN})
        get_filename_component(ABS_FIL ${FIL} ABSOLUTE)
        get_filename_component(FIL_WE ${FIL} NAME_WE)

        list(APPEND ${SRCS} "${CMAKE_CURRENT_BINARY_DIR}/${FIL_WE}.grpc.pb.cc")
        list(APPEND ${HDRS} "${CMAKE_CURRENT_BINARY_DIR}/${FIL_WE}.grpc.pb.h")

        add_custom_command(
            OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/${FIL_WE}.grpc.pb.cc"
                   "${CMAKE_CURRENT_BINARY_DIR}/${FIL_WE}.grpc.pb.h"
            COMMAND "${CMAKE_COMMAND}"  #FIXME: use conan binary component
            ARGS -E env "DYLD_LIBRARY_PATH=${Protobuf_LIB_DIRS}:${CONAN_LIB_DIRS}:${Protobuf_LIB_DIRS_RELEASE}:${Protobuf_LIB_DIRS_DEBUG}:${Protobuf_LIB_DIRS_RELWITHDEBINFO}:${Protobuf_LIB_DIRS_MINSIZEREL}"
                 protoc
                 --grpc_out=${CMAKE_CURRENT_BINARY_DIR}
                 --plugin=protoc-gen-grpc=${GRPC_CPP_PLUGIN}
                 ${_protobuf_include_path} ${ABS_FIL}
            DEPENDS ${ABS_FIL} ${PROTOC_PROGRAM}
            COMMENT "Running gRPC cpp protocol buffer compiler on ${FIL}"
            VERBATIM)
    endforeach()

    set_source_files_properties(${${SRCS}} ${${HDRS}} PROPERTIES GENERATED TRUE)
    set(${SRCS} ${${SRCS}} PARENT_SCOPE)
    set(${HDRS} ${${HDRS}} PARENT_SCOPE)
endfunction()

protobuf_generate_cpp(hw_proto_srcs hw_proto_hdrs helloworld.proto)
protobuf_generate_grpc_cpp(hw_grpc_srcs hw_grpc_hdrs helloworld.proto)

add_executable(greeter_client_server greeter_client_server.cc ${hw_proto_srcs} ${hw_proto_hdrs} ${hw_grpc_srcs} ${hw_grpc_hdrs})
target_include_directories(greeter_client_server PRIVATE ${CMAKE_BINARY_DIR})
target_link_libraries(greeter_client_server PRIVATE gRPC::grpc++_unsecure)