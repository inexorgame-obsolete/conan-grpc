from conans import ConanFile, CMake, tools
import os


class grpcConan(ConanFile):
    name = "grpc"
    version = "1.15.0-pre1"
    description = "Google's RPC library and framework."
    url = "https://github.com/inexorgame/conan-grpc"
    homepage = "https://github.com/grpc/grpc"
    license = "Apache-2.0"
    requires = "zlib/1.2.11@conan/stable", "OpenSSL/1.0.2o@conan/stable", "protobuf/3.6.1@bincrafters/stable", "c-ares/1.14.0@conan/stable"
    settings = "os", "compiler", "build_type", "arch"
    options = {
            # "shared": [True, False],
            "fPIC": [True, False],
            "build_codegen": [True, False],
            "build_csharp_ext": [True, False],
            "build_tests": [True, False]
    }
    default_options = '''fPIC=True
    build_codegen=True
    build_csharp_ext=False
    build_tests=False
    '''

    exports_sources = "CMakeLists.txt",
    generators = "cmake"
    short_paths = True  # Otherwise some folders go out of the 260 chars path length scope rapidly (on windows)

    source_subfolder = "source_subfolder"
    build_subfolder = "build_subfolder"

    def configure(self):
        if self.settings.os == "Windows" and self.settings.compiler == "Visual Studio":
            del self.options.fPIC
            compiler_version = int(str(self.settings.compiler.version))
            if compiler_version < 14:
                raise tools.ConanException("gRPC can only be built with Visual Studio 2015 or higher.")

    def source(self):
        archive_url = "https://github.com/grpc/grpc/archive/v{}.zip".format(self.version)
        tools.get(archive_url, sha256="c24a8c23eb41bd2f210424f329abdeefbedebd78361e0832213ad87920bd57f2")
        os.rename("grpc-{!s}".format(self.version), self.source_subfolder)

        # cmake_name = "{}/CMakeLists.txt".format(self.source_subfolder)

        # Parts which should be options:
        # grpc_cronet
        # grpc++_cronet
        # grpc_unsecure (?)
        # grpc++_unsecure (?)
        # grpc++_reflection
        # gen_hpack_tables (?)
        # gen_legal_metadata_characters (?)
        # grpc_csharp_plugin
        # grpc_node_plugin
        # grpc_objective_c_plugin
        # grpc_php_plugin
        # grpc_python_plugin
        # grpc_ruby_plugin

    def build_requirements(self):
        if self.options.build_tests:
            self.build_requires("benchmark/1.4.1@inexorgame/stable")
            self.build_requires("gflags/2.2.1@bincrafters/stable")

    def _configure_cmake(self):
        cmake = CMake(self)

        # This doesn't work yet as one would expect, because the install target builds everything
        # and we need the install target because of the generated CMake files
        #
        #   enable_mobile=False # Enables iOS and Android support
        #   non_cpp_plugins=False # Enables plugins such as --java-out and --py-out (if False, only --cpp-out is possible)
        #
        # cmake.definitions['CONAN_ADDITIONAL_PLUGINS'] = "ON" if self.options.build_csharp_ext else "OFF"
        #
        # Doesn't work yet for the same reason as above
        #
        # cmake.definitions['CONAN_ENABLE_MOBILE'] = "ON" if self.options.build_csharp_ext else "OFF"


        cmake.definitions['gRPC_BUILD_CODEGEN'] = "ON" if self.options.build_codegen else "OFF"
        cmake.definitions['gRPC_BUILD_CSHARP_EXT'] = "ON" if self.options.build_csharp_ext else "OFF"
        cmake.definitions['gRPC_BUILD_TESTS'] = "ON" if self.options.build_tests else "OFF"

        # We need the generated cmake/ files (bc they depend on the list of targets, which is dynamic)
        cmake.definitions['gRPC_INSTALL'] = "ON"
        # cmake.definitions['CMAKE_INSTALL_PREFIX'] = self.build_subfolder

        # tell grpc to use the find_package versions
        cmake.definitions['gRPC_CARES_PROVIDER'] = "package"
        cmake.definitions['gRPC_ZLIB_PROVIDER'] = "package"
        cmake.definitions['gRPC_SSL_PROVIDER'] = "package"
        cmake.definitions['gRPC_PROTOBUF_PROVIDER'] = "package"

        # Workaround for https://github.com/grpc/grpc/issues/11068
        if self.options.build_tests:
            cmake.definitions['gRPC_GFLAGS_PROVIDER'] = "package"
            cmake.definitions['gRPC_BENCHMARK_PROVIDER'] = "package"
        else:
            cmake.definitions['gRPC_GFLAGS_PROVIDER'] = "none"
            cmake.definitions['gRPC_BENCHMARK_PROVIDER'] = "none"

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
        self.cpp_info.libs = ["grpc", "grpc++", "grpc_unsecure", "grpc++_unsecure", "gpr", "address_sorting"]
        if self.settings.compiler == "Visual Studio":
            self.cpp_info.libs += ["wsock32", "ws2_32"]
