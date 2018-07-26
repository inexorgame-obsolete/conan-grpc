from conans import ConanFile, CMake, tools
import os


class grpcConan(ConanFile):
    name = "grpc"
    version = "1.14.0-pre1"
    description = "Google's RPC library and framework."
    url = "https://github.com/inexorgame/conan-grpc"
    homepage = "https://github.com/grpc/grpc"
    license = "Apache-2.0"
    requires = "zlib/1.2.11@conan/stable", "OpenSSL/1.0.2o@conan/stable", "protobuf/3.5.2@bincrafters/stable", "gflags/2.2.1@bincrafters/stable", "c-ares/1.14.0@conan/stable", "google_benchmark/1.4.1@inexorgame/stable"
    settings = "os", "compiler", "build_type", "arch"
    options = {
            "shared": [True, False],
            "enable_mobile": [True, False],  # Enables iOS and Android support
            "non_cpp_plugins": [True, False],  # Enables plugins such as --java-out and --py-out (if False, only --cpp-out is possible)
            "build_csharp_ext": [True, False]
            }
    default_options = '''shared=False
    enable_mobile=False
    non_cpp_plugins=False
    build_csharp_ext=False
    '''
    exports_sources = "CMakeLists.txt",
    generators = "cmake"
    short_paths = True  # Otherwise some folders go out of the 260 chars path length scope rapidly (on windows)

    source_subfolder = "source_subfolder"
    build_subfolder = "build_subfolder"

    def source(self):
        archive_url = "https://github.com/grpc/grpc/archive/v{}.zip".format(self.version)
        tools.get(archive_url, sha256="7f9431ffc65957989b361bbadb1fa1afe345abf67cf2a0315f8f9d84d2e70611")
        os.rename("grpc-{!s}".format(self.version), self.source_subfolder)

        cmake_name = "{}/CMakeLists.txt".format(self.source_subfolder)

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
        cmake = CMake(self)

        # This doesn't work yet as one would expect, because the install target builds everything
        # and we need the install target because of the generated CMake files
        if self.options.non_cpp_plugins:
            cmake.definitions['CONAN_ADDITIONAL_PLUGINS'] = "ON"
        else:
            cmake.definitions['CONAN_ADDITIONAL_PLUGINS'] = "OFF"

        # Doesn't work yet for the same reason as above
        if self.options.enable_mobile:
            cmake.definitions['CONAN_ENABLE_MOBILE'] = "ON"

        if self.options.build_csharp_ext:
            cmake.definitions['gRPC_BUILD_CSHARP_EXT'] = "ON"
        else:
            cmake.definitions['gRPC_BUILD_CSHARP_EXT'] = "OFF"


        # We need the generated cmake/ files (bc they depend on the list of targets, which is dynamic)
        cmake.definitions['gRPC_INSTALL'] = "ON"
        # cmake.definitions['CMAKE_INSTALL_PREFIX'] = self.build_subfolder

        # tell grpc to use the find_package versions
        cmake.definitions['gRPC_CARES_PROVIDER'] = "package"
        cmake.definitions['gRPC_ZLIB_PROVIDER'] = "package"
        cmake.definitions['gRPC_SSL_PROVIDER'] = "package"
        cmake.definitions['gRPC_PROTOBUF_PROVIDER'] = "package"
        cmake.definitions['gRPC_GFLAGS_PROVIDER'] = "package"
        cmake.definitions['gRPC_BENCHMARK_PROVIDER'] = "package"

        cmake.configure(build_folder=self.build_subfolder)
        return cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        cmake = self._configure_cmake()
        cmake.install()

        self.copy(pattern="LICENSE", dst="licenses")
        self.copy('*', dst='include', src='{}/include'.format(self.source_subfolder))
        self.copy('*.cmake', dst='lib', src='{}/lib'.format(self.build_subfolder), keep_path=True)
        self.copy("*.lib", dst="lib", src="", keep_path=False)
        self.copy("*.a", dst="lib", src="", keep_path=False)
        self.copy("*", dst="bin", src="bin")
        self.copy("*.dll", dst="bin", keep_path=False)
        self.copy("*.so", dst="lib", keep_path=False)

    def package_info(self):
        self.cpp_info.libs = ["grpc", "grpc++", "grpc_unsecure", "grpc++_unsecure", "gpr"]
        if self.settings.compiler == "Visual Studio":
            self.cpp_info.libs += ["wsock32", "ws2_32"]
