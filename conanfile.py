from conans import ConanFile, CMake, tools
import os
import shutil


class gRPCConan(ConanFile):
    name = "gRPC"
    version = "1.1.0-dev" # Nov 8
    folder = "grpc-31606bdb34474d8728350ad45baf0e91b590b041"
    url = "https://github.com/inexor-game/conan-grpc.git"
    license = "BSD-3Clause"
    requires = "zlib/1.2.8@lasote/stable", "OpenSSL/1.0.2i@lasote/stable", "Protobuf/3.1.0@a_teammate/testing"
    settings = "os", "compiler", "build_type", "arch"
    options = {
            "shared": [True, False],
            "enable_mobile": [True, False], # Enables iOS and Android support
            "non_cpp_plugins":[True, False] # Enables plugins such as --java-out and --py-out (if False, only --cpp-out is possible)
            }
    default_options = '''shared=False
    enable_mobile=False
    non_cpp_plugins=False
    '''
    generators = "cmake"
    short_paths = True # Otherwise some folders go out of the 260 chars path length scope rapidly (on windows)

    def source(self):
        tools.download("https://github.com/grpc/grpc/archive/31606bdb34474d8728350ad45baf0e91b590b041.zip", "grpc.zip")
        tools.unzip("grpc.zip")
        os.unlink("grpc.zip")
        cmake_name = "%s/CMakeLists.txt" % self.folder
        
        # tell grpc to use our deps and flags
        tools.replace_in_file(cmake_name, "project(${PACKAGE_NAME} C CXX)", '''project(${PACKAGE_NAME} C CXX)
        include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
        conan_basic_setup()''')
        tools.replace_in_file(cmake_name, "\"module\" CACHE STRING ", '''\"package\" CACHE STRING ''') # tell grpc to use the find_package version
        # never install manually, but let conan do it
        tools.replace_in_file(cmake_name, "gRPC_INSTALL ON", "gRPC_INSTALL OFF")
        tools.replace_in_file(cmake_name, '''  install(FILES ${_hdr}
    DESTINATION "${CMAKE_INSTALL_INCLUDEDIR}/${_path}"
  )''', '''  # install(FILES ${_hdr} # COMMENTED BY CONAN
    # DESTINATION "${CMAKE_INSTALL_INCLUDEDIR}/${_path}"
  # )''')
        
        # Add some CMake Variables (effectively commenting out stuff we do not support)
        tools.replace_in_file(cmake_name, "add_library(grpc_cronet", '''if(CONAN_ENABLE_MOBILE)
        add_library(grpc_cronet''')
        tools.replace_in_file(cmake_name, "add_library(grpc_unsecure", '''endif(CONAN_ENABLE_MOBILE)
        add_library(grpc_unsecure''')
        tools.replace_in_file(cmake_name, "add_library(grpc++_cronet", '''if(CONAN_ENABLE_MOBILE)
        add_library(grpc++_cronet''')
        tools.replace_in_file(cmake_name, "add_library(grpc++_reflection", '''endif(CONAN_ENABLE_MOBILE)
        if(CONAN_ENABLE_REFLECTION_LIBS)
        add_library(grpc++_reflection''')
        tools.replace_in_file(cmake_name, "add_library(grpc++_unsecure", '''endif(CONAN_ENABLE_REFLECTION_LIBS)
        add_library(grpc++_unsecure''')
        tools.replace_in_file(cmake_name, "add_library(grpc_csharp_ext", '''if(CONAN_ADDITIONAL_PLUGINS)
        add_library(grpc_csharp_ext''')
        tools.replace_in_file(cmake_name, "add_executable(gen_hpack_tables", '''endif(CONAN_ADDITIONAL_PLUGINS)
        if(CONAN_ADDITIONAL_BINS)
        add_executable(gen_hpack_tables''')
        tools.replace_in_file(cmake_name, "add_executable(grpc_cpp_plugin", '''endif(CONAN_ADDITIONAL_BINS)
        add_executable(grpc_cpp_plugin''')
        tools.replace_in_file(cmake_name, "add_executable(grpc_csharp_plugin", '''if(CONAN_ADDITIONAL_PLUGINS)
        add_executable(grpc_csharp_plugin''')
        tools.replace_in_file(cmake_name, '''target_link_libraries(grpc_ruby_plugin
  ${_gRPC_PROTOBUF_PROTOC_LIBRARIES}
  grpc_plugin_support
)''', '''target_link_libraries(grpc_ruby_plugin
  ${_gRPC_PROTOBUF_PROTOC_LIBRARIES}
  grpc_plugin_support
)
endif(CONAN_ADDITIONAL_PLUGINS)''')

    def build(self):
        cmake = CMake(self.settings)
        self.run('cmake %s/%s %s' % (self.conanfile_directory, self.folder, cmake.command_line))
        self.run("cmake --build . %s" % cmake.build_config)

    def package(self):
        self.copy('*', dst='include', src='include')
        self.copy("*.lib", dst="lib", src="", keep_path=False)
        self.copy("*.a", dst="lib", src="", keep_path=False)
        self.copy("*", dst="bin", src="bin")
        self.copy("*.dll", dst="bin", keep_path=False)
        self.copy("*.so", dst="lib", keep_path=False)

    def package_info(self):
        self.cpp_info.libs = ["gpr", "grpc", "grpc++", "grpc_unsecure", "grpc++_unsecure"]
        if self.settings.compiler == "Visual Studio":
            self.cpp_info.libs += ["wsock32", "ws2_32"]
