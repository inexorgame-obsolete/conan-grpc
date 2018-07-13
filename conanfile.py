from conans import ConanFile, CMake, tools
import os


class grpcConan(ConanFile):
    name = "grpc"
    version = "1.13.0"
    description = "Google's RPC library and framework."
    url = "https://github.com/inexorgame/conan-grpc"
    homepage = "https://github.com/grpc/grpc"
    license = "Apache-2.0"
    requires = "zlib/1.2.11@conan/stable", "OpenSSL/1.0.2o@conan/stable", "protobuf/3.5.2@bincrafters/stable", "gflags/2.2.1@bincrafters/stable", "c-ares/1.14.0@conan/stable", "google_benchmark/1.4.1@inexorgame/stable"
    settings = "os", "compiler", "build_type", "arch"
    options = {
            "shared": [True, False],
            "enable_mobile": [True, False],  # Enables iOS and Android support
            "non_cpp_plugins": [True, False]  # Enables plugins such as --java-out and --py-out (if False, only --cpp-out is possible)
            }
    default_options = '''shared=False
    enable_mobile=False
    non_cpp_plugins=False
    '''
    generators = "cmake"
    short_paths = True  # Otherwise some folders go out of the 260 chars path length scope rapidly (on windows)

    source_subfolder = "source_subfolder"
    build_subfolder = "build_subfolder"

    def source(self):
        archive_url = "https://github.com/grpc/grpc/archive/v{}.zip".format(self.version)
        tools.get(archive_url, sha256="a44cdd8f2b48b7356f9e1dfbb17d8b1967fea7cd71abfb587f25915904f27f87")
        os.rename("grpc-{!s}".format(self.version), self.source_subfolder)

        cmake_name = "{}/CMakeLists.txt".format(self.source_subfolder)

        # tell grpc to use our deps and flags
        tools.replace_in_file(cmake_name, "project(${PACKAGE_NAME} C CXX)", '''project(${PACKAGE_NAME} C CXX)
        include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
        conan_basic_setup()''')

        # skip installing the headers, TODO: use these!
        tools.replace_in_file(cmake_name, '''  install(FILES ${{_hdr}}{0!s}    DESTINATION "${{gRPC_INSTALL_INCLUDEDIR}}/${{_path}}"{0!s}  ){0!s}'''.format('\n'), '''  # install(FILES ${{_hdr}}{0!s}    # DESTINATION "${{gRPC_INSTALL_INCLUDEDIR}}/${{_path}}"{0!s}  # ){0!s}'''.format('\n'))

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
        # tools.replace_in_file(cmake_name, "add_library(grpc_csharp_ext", '''if(CONAN_ADDITIONAL_PLUGINS)
        # add_library(grpc_csharp_ext''') # not available anymore in v1.1.0
        # tools.replace_in_file(cmake_name, "add_executable(gen_hpack_tables", '''endif(CONAN_ADDITIONAL_PLUGINS)
        tools.replace_in_file(cmake_name, "add_executable(gen_hpack_tables", '''
        if(CONAN_ADDITIONAL_BINS)
        add_executable(gen_hpack_tables''')
        tools.replace_in_file(cmake_name, "add_executable(gen_legal_metadata_characters", '''endif(CONAN_ADDITIONAL_BINS)
        add_executable(gen_legal_metadata_characters''')
        tools.replace_in_file(cmake_name, "add_executable(grpc_csharp_plugin", '''if(CONAN_ADDITIONAL_PLUGINS)
        add_executable(grpc_csharp_plugin''')

        tools.replace_in_file(cmake_name, '''  install(TARGETS grpc_ruby_plugin EXPORT gRPCTargets{0!s}    RUNTIME DESTINATION ${{gRPC_INSTALL_BINDIR}}{0!s}    LIBRARY DESTINATION ${{gRPC_INSTALL_LIBDIR}}{0!s}    ARCHIVE DESTINATION ${{gRPC_INSTALL_LIBDIR}}{0!s}  ){0!s}endif()'''.format('\n'), '''  install(TARGETS grpc_ruby_plugin EXPORT gRPCTargets{0!s}    RUNTIME DESTINATION ${{gRPC_INSTALL_BINDIR}}{0!s}    LIBRARY DESTINATION ${{gRPC_INSTALL_LIBDIR}}{0!s}    ARCHIVE DESTINATION ${{gRPC_INSTALL_LIBDIR}}{0!s}  ){0!s}endif(){0!s}endif(CONAN_ADDITIONAL_PLUGINS)'''.format('\n'))

    def _configure_cmake(self):
        tmp_install_dir = "{}/install".format(self.build_folder)
        os.makedirs(tmp_install_dir, exist_ok=True)

        cmake = CMake(self)

        if self.options.non_cpp_plugins:
            cmake.definitions['CONAN_ADDITIONAL_PLUGINS'] = "ON"
            # cmake.definitions['gRPC_BUILD_CSHARP_EXT'] = "ON"  # This will be available post-1.13.0
        else:
            cmake.definitions['CONAN_ADDITIONAL_PLUGINS'] = "OFF"
            # cmake.definitions['gRPC_BUILD_CSHARP_EXT'] = "OFF"

        if self.options.enable_mobile:
            cmake.definitions['CONAN_ENABLE_MOBILE'] = "ON"

        # We need the generated cmake/ files (bc they depend on the list of targets, which is dynamic)
        cmake.definitions['gRPC_INSTALL'] = "ON"
        cmake.definitions['CMAKE_INSTALL_PREFIX'] = tmp_install_dir

        # tell grpc to use the find_package versions
        cmake.definitions['gRPC_CARES_PROVIDER'] = "package"
        cmake.definitions['gRPC_ZLIB_PROVIDER'] = "package"
        cmake.definitions['gRPC_SSL_PROVIDER'] = "package"
        cmake.definitions['gRPC_PROTOBUF_PROVIDER'] = "package"
        cmake.definitions['gRPC_GFLAGS_PROVIDER'] = "package"
        cmake.definitions['gRPC_BENCHMARK_PROVIDER'] = "package"

        cmake.configure(source_folder='{}'.format(self.source_subfolder))
        return cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

        # Patch the generated findGRPC .cmake files:
        # cmake_find_folder = "{}/cmake/gRPC".format(self.get_install_lib_path())
        # cmake_find_file = "{}/gRPCTargets.cmake".format(cmake_find_folder)
        # tools.replace_in_file(cmake_find_file, 'get_filename_component(_IMPORT_PREFIX "${_IMPORT_PREFIX}" PATH)', '''get_filename_component(_IMPORT_PREFIX "${_IMPORT_PREFIX}" PATH)
        # set(_IMPORT_PREFIX ${CONAN_GRPC_ROOT}) # NOTE: ADDED by conan''')

    def package(self):
        cmake = self._configure_cmake()
        cmake.install()

        cmake_folder = "{}/cmake/gRPC".format(self.get_install_lib_path())
        cmake_files = ["gRPCConfig.cmake", "gRPCConfigVersion.cmake", "gRPCTargets.cmake"]
        for file in cmake_files:
            self.copy(file, dst='.', src=cmake_folder)
        # Copy the build_type specific file only for our used one:
        self.copy("gRPCTargets-{}.cmake".format("debug" if self.settings.build_type == "Debug" else "release"), dst=".", src=cmake_folder)

        self.copy('*', dst='include', src='{}/include'.format(self.source_subfolder))
        self.copy("*.lib", dst="lib", src="", keep_path=False)
        self.copy("*.a", dst="lib", src="", keep_path=False)
        self.copy("*", dst="bin", src="bin")
        self.copy("*.dll", dst="bin", keep_path=False)
        self.copy("*.so", dst="lib", keep_path=False)

    def package_info(self):
        self.cpp_info.libs = ["grpc", "grpc++", "grpc_unsecure", "grpc++_unsecure", "gpr"]
        if self.settings.compiler == "Visual Studio":
            self.cpp_info.libs += ["wsock32", "ws2_32"]

    def get_install_lib_path(self):
        install_path = "{}/install".format(self.build_subfolder)
        if os.path.isfile("{}/lib/cmake/gRPC/gRPCTargets.cmake".format(install_path)):
            return "{}/lib".format(install_path)
        elif os.path.isfile("{}/lib64/cmake/gRPC/gRPCTargets.cmake".format(install_path)):
            return "{}/lib64".format(install_path)
        # its "{}/install/{{lib|lib64}}/cmake/gRPC/gRPCTargets.cmake".format(self.build_folder)
