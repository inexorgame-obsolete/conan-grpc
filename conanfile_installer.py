#!/usr/bin/env python
from conans import CMake
from conanfile_base import ConanFileBase
from conans.errors import ConanInvalidConfiguration
import os

class grpcConan(ConanFileBase):
    settings="os","arch","compiler","build_type"
    name ="grpc_installer"
    version=ConanFileBase.version
    protobuf_version=ConanFileBase.protobuf_version

    #just to satisfy cmake..
    build_requires = (
        "zlib/1.2.11",
        "openssl/1.0.2s",
        #TODO make it depend on grpc ??
        #"@bincrafters/stable"
        #"protoc_installer/{}@bincrafters/stable".format(ConanFileBase.protobuf_version),
        #"c-ares/1.15.0"
        "c-ares/1.15.0@conan/stable"
    )
    options = {
        "build_jwt" : [True,False],
    }

    default_options = {
        "build_jwt" : False,
    }

    plugins=[
        'grpc_python_plugin',
        'grpc_php_plugin',
        'grpc_objective_c_plugin',
        'grpc_node_plugin',
        'grpc_csharp_plugin',
        'grpc_cpp_plugin'
    ]

    def requirements(self):
        self.requires.add("protobuf/{}@bincrafters/stable".format(ConanFileBase.protobuf_version))
        self.requires.add("protoc_installer/{}@bincrafters/stable".format(ConanFileBase.protobuf_version))


    def configure(self):
        if self.options.build_jwt:
            plugins.append('grpc_verify_jwt','grpc_create_jwt')
        if self.settings.os == "Windows" and self.settings.compiler == "Visual Studio":
            del self.options.fPIC
            compiler_version = int(str(self.settings.compiler.version))
            if compiler_version < 14:
                raise ConanInvalidConfiguration("gRPC can only be built with Visual Studio 2015 or higher.")

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


        cmake.definitions['gRPC_BUILD_CODEGEN'] = "ON"
        cmake.definitions['gRPC_BUILD_CSHARP_EXT'] = "OFF"
        cmake.definitions['gRPC_BUILD_TESTS'] = "OFF"

        # We need the generated cmake/ files (bc they depend on the list of targets, which is dynamic)
        cmake.definitions['gRPC_INSTALL'] = "ON"
        # cmake.definitions['CMAKE_INSTALL_PREFIX'] = self._build_subfolder

        # tell grpc to use the find_package versions
        cmake.definitions['gRPC_CARES_PROVIDER'] = "package"
        cmake.definitions['gRPC_ZLIB_PROVIDER'] = "package"
        cmake.definitions['gRPC_SSL_PROVIDER'] = "package"
        cmake.definitions['gRPC_PROTOBUF_PROVIDER'] = "package"

        # Workaround for https://github.com/grpc/grpc/issues/11068
        cmake.definitions['gRPC_GFLAGS_PROVIDER'] = "none"
        cmake.definitions['gRPC_BENCHMARK_PROVIDER'] = "none"

        # Compilation on minGW GCC requires to set _WIN32_WINNTT to at least 0x600
        # https://github.com/grpc/grpc/blob/109c570727c3089fef655edcdd0dd02cc5958010/include/grpc/impl/codegen/port_platform.h#L44
        if self.settings.os == "Windows" and self.settings.compiler == "gcc":
            cmake.definitions["CMAKE_CXX_FLAGS"] = "-D_WIN32_WINNT=0x600"
            cmake.definitions["CMAKE_C_FLAGS"] = "-D_WIN32_WINNT=0x600"

        cmake.configure(build_folder=self._build_subfolder)
        return cmake

    def build(self):
        cmake = self._configure_cmake()
        #does conan support multiple targets ??
        for plugs in self.plugins:
            cmake.build(target=plugs)

    def package(self):
        self.copy("*", dst="bin", src="build_subfolder/bin")

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.arch
        self.info.include_build_settings()

    def package_info(self):
        self.env_info.PATH.append(os.path.join(self.package_folder, "bin"))
