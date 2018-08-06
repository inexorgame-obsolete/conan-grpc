cmake_minimum_required(VERSION 2.8.11)
project(test_package)

set(CMAKE_VERBOSE_MAKEFILE TRUE)

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()

if (MSVC)
  add_definitions(/MP)
endif (MSVC)

find_package(gRPC REQUIRED)

find_program(GRPC_GRPC_CPP_PLUGIN grpc_cpp_plugin PATHS ${CONAN_BIN_DIRS_GRPC} NO_SYSTEM_ENVIRONMENT_PATH NO_CMAKE_SYSTEM_PATH )
function(GRPC_GENERATE_CPP SRCS HDRS)
  if(NOT ARGN)
    message(SEND_ERROR "Error: GRPC_GENERATE_CPP() called without any proto files")
    return()
  endif()

  if(PROTOBUF_GENERATE_CPP_APPEND_PATH)
    # Create an include path for each file specified
    foreach(FIL ${ARGN})
      get_filename_component(ABS_FIL ${FIL} ABSOLUTE)
      get_filename_component(ABS_PATH ${ABS_FIL} PATH)
      list(FIND _protobuf_include_path ${ABS_PATH} _contains_already)
      if(${_contains_already} EQUAL -1)
          list(APPEND _protobuf_include_path -I ${ABS_PATH})
      endif()
    endforeach()
  else()
    set(_protobuf_include_path -I ${CMAKE_CURRENT_SOURCE_DIR})
  endif()

  if(DEFINED Protobuf_IMPORT_DIRS)
    foreach(DIR ${Protobuf_IMPORT_DIRS})
      get_filename_component(ABS_PATH ${DIR} ABSOLUTE)
      list(FIND _protobuf_include_path ${ABS_PATH} _contains_already)
      if(${_contains_already} EQUAL -1)
          list(APPEND _protobuf_include_path -I ${ABS_PATH})
      endif()
    endforeach()
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
      COMMAND  ${Protobuf_PROTOC_EXECUTABLE}
          --plugin=protoc-gen-grpc=${GRPC_GRPC_CPP_PLUGIN}
          --grpc_out=${CMAKE_CURRENT_BINARY_DIR}
          ${_protobuf_include_path}
          ${ABS_FIL}
      DEPENDS ${ABS_FIL} ${Protobuf_PROTOC_EXECUTABLE} ${GRPC_GRPC_CPP_PLUGIN}
      COMMENT "Running C++ protocol buffer compiler with the GRPC plugin on ${FIL}"
      VERBATIM )
  endforeach()

  set_source_files_properties(${${SRCS}} ${${HDRS}} PROPERTIES GENERATED TRUE)
  set(${SRCS} ${${SRCS}} PARENT_SCOPE)
  set(${HDRS} ${${HDRS}} PARENT_SCOPE)
endfunction()

PROTOBUF_GENERATE_CPP(SRC_FILE HEADER_FILE helloworld.proto)
GRPC_GENERATE_CPP(GRPC_SRC_FILE GRPC_HEADER_FILE helloworld.proto)

if(NOT MSVC)
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11")
else()
  add_definitions(-D_WIN32_WINNT=0x600)
endif()

include_directories(${Protobuf_INCLUDE_DIRS} ${CMAKE_CURRENT_BINARY_DIR}) # CMAKE_CURRENT_BINARY_DIR is where our generated files are (.pb.hpp)
add_executable(${PROJECT_NAME} greeter_client.cc ${SRC_FILE} ${HEADER_FILE} ${GRPC_SRC_FILE} ${GRPC_HEADER_FILE})
if(NOT TARGET protobuf::libprotobuf)
    message(FATAL_ERROR "WE DIDN'T FIND LIBPROTOBUFS IMPORT TARGET (Protobuf_LIBRARIES = ${Protobuf_LIBRARIES})")
endif()
target_link_libraries(${PROJECT_NAME} ${CONAN_LIBS}) # This is still faulty: protobuf::libprotobuf gRPC::grpc++ gRPC::grpc does not work (neither with gRPC::gpr OpenSSL::SSL added)
