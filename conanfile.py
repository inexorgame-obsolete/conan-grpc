from conans import ConanFile, CMake, tools
from conans.errors import ConanInvalidConfiguration
from conans.tools import Version
import os
import re
import json


class grpcConan(ConanFile):
    name = "grpc"
    description = "Google's RPC library and framework."
    topics = ("conan", "grpc", "rpc")
    url = "https://github.com/inexorgame/conan-grpc"
    homepage = "https://github.com/grpc/grpc"
    license = "Apache-2.0"
    exports_sources = ["CMakeLists.txt"]
    generators = "cmake", "cmake_find_package_multi"
    short_paths = True

    settings = "os", "arch", "compiler", "build_type"
    # TODO: Add shared option
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "build_codegen": [True, False],
        "build_csharp_ext": [True, False],
        "build_grpc_cpp_plugin": [True, False],
        "build_grpc_csharp_plugin": [True, False],
        "build_grpc_node_plugin": [True, False],
        "build_grpc_objective_c_plugin": [True, False],
        "build_grpc_php_plugin": [True, False],
        "build_grpc_python_plugin": [True, False],
        "build_grpc_ruby_plugin": [True, False],
        "use_proto_lite": [True, False]
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "build_codegen": True,
        "build_csharp_ext": False,
        "build_grpc_cpp_plugin": True,
        "build_grpc_csharp_plugin": False,
        "build_grpc_node_plugin": False,
        "build_grpc_objective_c_plugin": False,
        "build_grpc_php_plugin": False,
        "build_grpc_python_plugin": True,
        "build_grpc_ruby_plugin": False,
        "use_proto_lite": False
    }

    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    requires = (
        "zlib/1.2.11",
        "openssl/1.1.1h",
        "protobuf/3.12.4",
        "c-ares/1.15.0",
        "abseil/20200225.3",
        "re2/20201001"
    )

    def configure(self):
        if self.settings.os == "Windows" and self.settings.compiler == "Visual Studio":
            del self.options.fPIC
            compiler_version = tools.Version(self.settings.compiler.version)
            if compiler_version < 14:
                raise ConanInvalidConfiguration("gRPC can only be built with Visual Studio 2015 or higher.")

    def config_options(self):
        pass
        # if protobuf not compiled with 'lite' library, delete use_proto_lite
        # if not self.options["protobuf"].lite:
        #    del self.options.use_proto_lite

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self._source_subfolder)

        cmake_path = os.path.join(self._source_subfolder, "CMakeLists.txt")

        # See #5
        tools.replace_in_file(cmake_path, "_gRPC_PROTOBUF_LIBRARIES", "CONAN_LIBS_PROTOBUF")

        # TODO Parts which should be options:
        # grpc_cronet
        # grpc++_cronet
        # grpc_unsecure (?)
        # grpc++_unsecure (?)
        # grpc++_reflection
        # gen_hpack_tables (?)
        # gen_legal_metadata_characters (?)

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

        cmake.verbose = True
        cmake.definitions['gRPC_BUILD_CODEGEN'] = self.options.build_codegen
        cmake.definitions['gRPC_BUILD_CSHARP_EXT'] = self.options.build_csharp_ext
        cmake.definitions['gRPC_BACKWARDS_COMPATIBILITY_MODE'] = "OFF"
        cmake.definitions['gRPC_BUILD_TESTS'] = "OFF"

        # We need the generated cmake/ files (bc they depend on the list of targets, which is dynamic)
        cmake.definitions['gRPC_INSTALL'] = "ON"
        # cmake.definitions['CMAKE_INSTALL_PREFIX'] = self._build_subfolder

        # tell grpc to use the find_package versions
        cmake.definitions['gRPC_ZLIB_PROVIDER'] = "package"
        cmake.definitions['gRPC_CARES_PROVIDER'] = "package"
        cmake.definitions['gRPC_RE2_PROVIDER'] = "package"
        cmake.definitions['gRPC_SSL_PROVIDER'] = "package"
        cmake.definitions['gRPC_PROTOBUF_PROVIDER'] = "package"
        cmake.definitions['gRPC_PROTOBUF_PACKAGE_TYPE'] = "MODULE"

        cmake.definitions['gRPC_ABSL_PROVIDER'] = "package"
        cmake.definitions['gRPC_USE_PROTO_LITE'] = self.options.get_safe("use_proto_lite")

        cmake.definitions['gRPC_BUILD_GRPC_CPP_PLUGIN'] = self.options.build_grpc_cpp_plugin
        cmake.definitions['gRPC_BUILD_GRPC_CSHARP_PLUGIN'] = self.options.build_grpc_csharp_plugin
        cmake.definitions['gRPC_BUILD_GRPC_NODE_PLUGIN'] = self.options.build_grpc_node_plugin
        cmake.definitions['gRPC_BUILD_GRPC_OBJECTIVE_C_PLUGIN'] = self.options.build_grpc_objective_c_plugin
        cmake.definitions['gRPC_BUILD_GRPC_PHP_PLUGIN'] = self.options.build_grpc_php_plugin
        cmake.definitions['gRPC_BUILD_GRPC_PYTHON_PLUGIN'] = self.options.build_grpc_python_plugin
        cmake.definitions['gRPC_BUILD_GRPC_RUBY_PLUGIN'] = self.options.build_grpc_ruby_plugin

        # see https://github.com/inexorgame/conan-grpc/issues/39
        if self.settings.os == "Windows":
            if not self.options["protobuf"].shared:
                cmake.definitions["Protobuf_USE_STATIC_LIBS"] = "ON"
            else:
                cmake.definitions["PROTOBUF_USE_DLLS"] = "ON"

        # Compilation on minGW GCC requires to set _WIN32_WINNTT to at least 0x600
        # https://github.com/grpc/grpc/blob/109c570727c3089fef655edcdd0dd02cc5958010/include/grpc/impl/codegen/port_platform.h#L44
        if self.settings.os == "Windows" and self.settings.compiler == "gcc":
            cmake.definitions["CMAKE_CXX_FLAGS"] = "-D_WIN32_WINNT=0x600"
            cmake.definitions["CMAKE_C_FLAGS"] = "-D_WIN32_WINNT=0x600"

        cmake.configure(build_folder=self._build_subfolder)
        return cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy(pattern="LICENSE", dst="licenses", src=self._source_subfolder)
        cmake = self._configure_cmake()
        cmake.install()

        cmake_folder = os.path.join(self.package_folder, "lib", "cmake")
        tools.rmdir(cmake_folder)

    def package_info(self):
        bindir = os.path.join(self.package_folder, "bin")
        self.output.info("Appending PATH environment variable: {}".format(bindir))
        self.env_info.PATH.append(bindir)

        system_libs = []
        if self.settings.os == "Macos" or self.settings.os == "iOS":
            system_libs = ["dl", "m", "pthread"]
        elif self.settings.os == "Linux":
            system_libs = ["dl", "m", "rt", "pthread"]
        elif self.settings.os == "Android":
            system_libs = ["dl", "m"]
        elif self.settings.os == "Windows":
            system_libs = ["wsock32", "ws2_32", "crypt32"]

        self.cpp_info.names["cmake_find_package"] = "gRPC"
        self.cpp_info.names["cmake_find_package_multi"] = "gRPC"

        self.cpp_info.components["address_sorting"].libs = ["address_sorting"]
        self.cpp_info.components["address_sorting"].system_libs = system_libs

        self.cpp_info.components["upb"].libs = ["upb"]
        self.cpp_info.components["upb"].system_libs = system_libs

        self.cpp_info.components["gpr"].libs = ["gpr"]
        self.cpp_info.components["gpr"].system_libs = system_libs
        if self.settings.os == "Android":
            self.cpp_info.components["gpr"].system_libs.append("log")
        self.cpp_info.components["gpr"].requires = ["abseil::absl_time", "abseil::absl_synchronization", "abseil::absl_strings", "abseil::absl_str_format", "abseil::absl_memory", "abseil::absl_base"]

        self.cpp_info.components["libgrpc"].libs = ["grpc"]
        self.cpp_info.components["libgrpc"].system_libs = system_libs
        self.cpp_info.components["libgrpc"].frameworks = ["CoreFoundation"]
        self.cpp_info.components["libgrpc"].requires = ["openssl::ssl", "openssl::crypto", "zlib::zlib", "c-ares::cares", "re2::re2", "address_sorting", "upb", "gpr", "abseil::absl_optional", "abseil::absl_strings", "abseil::absl_status", "abseil::absl_inlined_vector", "abseil::absl_flat_hash_set"]

        self.cpp_info.components["grpc_plugin_support"].libs = ["grpc_plugin_support"]
        self.cpp_info.components["grpc_plugin_support"].system_libs = system_libs
        self.cpp_info.components["grpc_plugin_support"].requires = ["protobuf::libprotoc", "protobuf::libprotobuf"]

        self.cpp_info.components["grpc_unsecure"].libs = ["grpc_unsecure"]
        self.cpp_info.components["grpc_unsecure"].system_libs = system_libs
        self.cpp_info.components["grpc_unsecure"].frameworks = ["CoreFoundation"]
        self.cpp_info.components["grpc_unsecure"].requires = ["zlib::zlib", "c-ares::cares", "re2::re2", "address_sorting", "upb", "abseil::absl_optional", "abseil::absl_strings", "abseil::absl_status", "abseil::absl_inlined_vector"]

        self.cpp_info.components["grpc++"].libs = ["grpc++"]
        self.cpp_info.components["grpc++"].system_libs = system_libs
        self.cpp_info.components["grpc++"].requires = ["protobuf::libprotobuf", "libgrpc", "gpr", "address_sorting", "upb"]

        # TODO: if codegen && not protobuf lite
        self.cpp_info.components["grpcpp_channelz"].libs = ["grpcpp_channelz"]
        self.cpp_info.components["grpcpp_channelz"].system_libs = system_libs
        self.cpp_info.components["grpcpp_channelz"].requires = ["protobuf::libprotobuf", "grpc++", "libgrpc", "gpr", "upb"]

        self.cpp_info.components["grpc++_alts"].libs = ["grpc++_alts"]
        self.cpp_info.components["grpc++_alts"].system_libs = system_libs
        self.cpp_info.components["grpc++_alts"].requires = ["protobuf::libprotobuf", "grpc++", "libgrpc", "gpr", "upb"]

        self.cpp_info.components["grpc++_error_details"].libs = ["grpc++_error_details"]
        self.cpp_info.components["grpc++_error_details"].system_libs = system_libs
        self.cpp_info.components["grpc++_error_details"].requires = ["protobuf::libprotobuf", "grpc++", "libgrpc", "gpr", "upb"]

        self.cpp_info.components["grpc++_reflection"].libs = ["grpc++_reflection"]
        self.cpp_info.components["grpc++_reflection"].system_libs = system_libs
        self.cpp_info.components["grpc++_reflection"].requires = ["protobuf::libprotobuf", "grpc++", "libgrpc", "gpr", "upb"]

        self.cpp_info.components["grpc++_unsecure"].libs = ["grpc++_unsecure"]
        self.cpp_info.components["grpc++_unsecure"].system_libs = system_libs
        self.cpp_info.components["grpc++_unsecure"].requires = ["protobuf::libprotobuf", "grpc++", "libgrpc", "gpr", "upb"]

        # TODO: add optional plugin components?
