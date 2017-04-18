from conans import ConanFile, CMake, tools
import os
import shutil


class gRPCConan(ConanFile):
    name = "gRPC"
    version = "1.1.0-dev" # Nov 8
    folder = "grpc-31606bdb34474d8728350ad45baf0e91b590b041"
    description = "Googles RPC framework in use by the Inexor game."
    url = "https://github.com/inexor-game/conan-grpc.git"
    license = "BSD-3Clause"
    requires = "zlib/1.2.8@lasote/stable", "OpenSSL/1.0.2j@lasote/stable", "Protobuf/3.1.0@inexorgame/stable"
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
        cmake_name = "{}/CMakeLists.txt".format(self.folder)
        
        # tell grpc to use our deps and flags
        tools.replace_in_file(cmake_name, "project(${PACKAGE_NAME} C CXX)", '''project(${PACKAGE_NAME} C CXX)
        include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
        conan_basic_setup()''')
        tools.replace_in_file(cmake_name, "\"module\" CACHE STRING ", '''\"package\" CACHE STRING ''') # tell grpc to use the find_package version
        # skip installing the headers, TODO: use these!
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
        tools.replace_in_file(cmake_name, '''install(TARGETS grpc_ruby_plugin EXPORT gRPCTargets
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
  )
endif()''', '''install(TARGETS grpc_ruby_plugin EXPORT gRPCTargets
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
  )
endif()
endif(CONAN_ADDITIONAL_PLUGINS)''')

    def build(self):
        tmp_install_dir = "{}/install".format(os.getcwd())
        os.mkdir(tmp_install_dir)
        args = ["-DgRPC_INSTALL=ON", '-DCMAKE_INSTALL_PREFIX="{}"'.format(tmp_install_dir)] # We need the generated cmake/ files (bc they depend on the list of targets, which is dynamic)
        if self.options.non_cpp_plugins:
            args += ["-DCONAN_ADDITIONAL_PLUGINS=ON"]
        if self.options.enable_mobile:
            args += ["-DCONAN_ENABLE_MOBILE=ON"]
        cmake = CMake(self.settings)
        self.run('cmake {0}/{1} {2} {3}'.format(self.conanfile_directory, self.folder, cmake.command_line, ' '.join(args)))
        self.run("cmake --build . --target install {}".format(cmake.build_config))


        # Patch the generated findGRPC .cmake files:
        cmake_find_folder = "{}/cmake/gRPC".format(self.get_install_lib_path())
        cmake_find_file = "{}/gRPCTargets.cmake".format(cmake_find_folder)
        tools.replace_in_file(cmake_find_file, 'get_filename_component(_IMPORT_PREFIX "${_IMPORT_PREFIX}" PATH)', '''get_filename_component(_IMPORT_PREFIX "${_IMPORT_PREFIX}" PATH)
        set(_IMPORT_PREFIX ${CONAN_GRPC_ROOT}) # NOTE: ADDED by conan''')

    def package(self):
        cmake_folder = "{}/cmake/gRPC".format(self.get_install_lib_path())
        cmake_files = ["gRPCConfig.cmake", "gRPCConfigVersion.cmake", "gRPCTargets.cmake"]
        for file in cmake_files:
            self.copy(file, dst='.', src=cmake_folder)
          # Copy the build_type specific file only for our used one:
        self.copy("gRPCTargets-{}.cmake".format("debug" if self.settings.build_type == "Debug" else "release"), dst=".", src=cmake_folder)

        self.copy('*', dst='include', src='{}/include'.format(self.folder))
        self.copy("*.lib", dst="lib", src="", keep_path=False)
        self.copy("*.a", dst="lib", src="", keep_path=False)
        self.copy("*", dst="bin", src="bin")
        self.copy("*.dll", dst="bin", keep_path=False)
        self.copy("*.so", dst="lib", keep_path=False)

    def package_info(self):
        self.cpp_info.libs = ["gpr", "grpc", "grpc++", "grpc_unsecure", "grpc++_unsecure"]
        if self.settings.compiler == "Visual Studio":
            self.cpp_info.libs += ["wsock32", "ws2_32"]

    def get_install_lib_path(self):
        install_path = "{}/install".format(os.getcwd())
        if os.path.isfile("{}/lib/cmake/gRPC/gRPCTargets.cmake".format(install_path)):
            return "{}/lib".format(install_path)
        elif os.path.isfile("{}/lib64/cmake/gRPC/gRPCTargets.cmake".format(install_path)):
            return "{}/lib64".format(install_path)
        # its "{}/install/{{lib|lib64}}/cmake/gRPC/gRPCTargets.cmake".format(os.getcwd())