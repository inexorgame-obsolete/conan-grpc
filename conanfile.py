from conans import ConanFile, CMake, tools
from conans.errors import ConanInvalidConfiguration
from conans.tools import Version
import os


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

    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "build_codegen": [True, False],
        "build_csharp_ext": [True, False],
        "build_cpp_plugin": [True, False],
        "build_csharp_plugin": [True, False],
        "build_node_plugin": [True, False],
        "build_objective_c_plugin": [True, False],
        "build_php_plugin": [True, False],
        "build_python_plugin": [True, False],
        "build_ruby_plugin": [True, False]
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "build_codegen": True,
        "build_csharp_ext": False,
        "build_cpp_plugin": True,
        "build_csharp_plugin": True,
        "build_node_plugin": True,
        "build_objective_c_plugin": True,
        "build_php_plugin": True,
        "build_python_plugin": True,
        "build_ruby_plugin": True,
    }

    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    requires = (
        "zlib/1.2.11",
        "openssl/1.1.1h",
        "protobuf/3.12.4",
        "c-ares/1.15.0",
        "abseil/20200225.3",
        "re2/20201101"
    )

    def configure(self):
        if self.settings.os == "Windows" and self.settings.compiler == "Visual Studio":
            compiler_version = tools.Version(self.settings.compiler.version)
            if compiler_version < 14:
                raise ConanInvalidConfiguration("gRPC can only be built with Visual Studio 2015 or higher.")
        if self.options.shared:
            if tools.is_apple_os(self.settings.os):
                raise ConanInvalidConfiguration("gRPC could not be built as shared library for Mac.")

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self._source_subfolder)

        cmake_path = os.path.join(self._source_subfolder, "CMakeLists.txt")

        # See #5
        tools.replace_in_file(cmake_path, "_gRPC_PROTOBUF_LIBRARIES", "CONAN_LIBS_PROTOBUF")

    def _configure_cmake(self):
        cmake = CMake(self)

        # This doesn't work yet as one would expect, because the install target builds everything
        # and we need the install target because of the generated CMake files
        #
        #   enable_mobile=False # Enables iOS and Android support
        #
        # cmake.definitions["CONAN_ENABLE_MOBILE"] = "ON" if self.options.build_csharp_ext else "OFF"

        cmake.definitions["gRPC_BUILD_CODEGEN"] = "ON" if self.options.build_codegen else "OFF"
        cmake.definitions["gRPC_BUILD_CSHARP_EXT"] = "ON" if self.options.build_csharp_ext else "OFF"
        cmake.definitions['gRPC_BACKWARDS_COMPATIBILITY_MODE'] = "OFF"
        cmake.definitions["gRPC_BUILD_TESTS"] = "OFF"

        # We need the generated cmake/ files (bc they depend on the list of targets, which is dynamic)
        cmake.definitions["gRPC_INSTALL"] = "ON"
        # cmake.definitions["CMAKE_INSTALL_PREFIX"] = self._build_subfolder

        # tell grpc to use the find_package versions
        cmake.definitions["gRPC_ABSL_PROVIDER"] = "package"
        cmake.definitions["gRPC_CARES_PROVIDER"] = "package"
        cmake.definitions["gRPC_ZLIB_PROVIDER"] = "package"
        cmake.definitions["gRPC_SSL_PROVIDER"] = "package"
        cmake.definitions["gRPC_PROTOBUF_PROVIDER"] = "package"
        cmake.definitions['gRPC_PROTOBUF_PACKAGE_TYPE'] = "MODULE"
        cmake.definitions["gRPC_RE2_PROVIDER"] = "package"

        cmake.definitions['gRPC_USE_PROTO_LITE'] = "OFF"
        if self.options["protobuf"].lite:
            raise ConanInvalidConfiguration("protobuf:lite is not handled properly in gRPC recipe")

        cmake.definitions["gRPC_BUILD_GRPC_CPP_PLUGIN"] = self.options.build_cpp_plugin
        cmake.definitions["gRPC_BUILD_GRPC_CSHARP_PLUGIN"] = self.options.build_csharp_plugin
        cmake.definitions["gRPC_BUILD_GRPC_NODE_PLUGIN"] = self.options.build_node_plugin
        cmake.definitions["gRPC_BUILD_GRPC_OBJECTIVE_C_PLUGIN"] = self.options.build_objective_c_plugin
        cmake.definitions["gRPC_BUILD_GRPC_PHP_PLUGIN"] = self.options.build_php_plugin
        cmake.definitions["gRPC_BUILD_GRPC_PYTHON_PLUGIN"] = self.options.build_python_plugin
        cmake.definitions["gRPC_BUILD_GRPC_RUBY_PLUGIN"] = self.options.build_ruby_plugin

        # see https://github.com/inexorgame/conan-grpc/issues/39
        # TODO: can we remove this now that CCI protobuf provides PROTOBUF_USE_DLLS ?
        if self.settings.os == "Windows":
            if not self.options["protobuf"].shared:
                cmake.definitions["Protobuf_USE_STATIC_LIBS"] = "ON"
            else:
                cmake.definitions["PROTOBUF_USE_DLLS"] = "ON"

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
        self.cpp_info.names["pkg_config"] = "gRPC"

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

        if self.options.build_codegen:  # and not use_proto_lite
            self.cpp_info.components["grpcpp_channelz"].libs = ["grpcpp_channelz"]
            self.cpp_info.components["grpcpp_channelz"].system_libs = system_libs
            self.cpp_info.components["grpcpp_channelz"].requires = ["protobuf::libprotobuf", "grpc++", "libgrpc", "gpr", "upb"]

        self.cpp_info.components["grpc++_alts"].libs = ["grpc++_alts"]
        self.cpp_info.components["grpc++_alts"].system_libs = system_libs
        self.cpp_info.components["grpc++_alts"].requires = ["protobuf::libprotobuf", "grpc++", "libgrpc", "gpr", "upb"]

        if self.options.build_codegen:
            self.cpp_info.components["grpc++_error_details"].libs = ["grpc++_error_details"]
            self.cpp_info.components["grpc++_error_details"].system_libs = system_libs
            self.cpp_info.components["grpc++_error_details"].requires = ["protobuf::libprotobuf", "grpc++", "libgrpc", "gpr", "upb"]

            self.cpp_info.components["grpc++_reflection"].libs = ["grpc++_reflection"]
            self.cpp_info.components["grpc++_reflection"].system_libs = system_libs
            self.cpp_info.components["grpc++_reflection"].requires = ["protobuf::libprotobuf", "grpc++", "libgrpc", "gpr", "upb"]

        self.cpp_info.components["grpc++_unsecure"].libs = ["grpc++_unsecure"]
        self.cpp_info.components["grpc++_unsecure"].system_libs = system_libs
        self.cpp_info.components["grpc++_unsecure"].requires = ["protobuf::libprotobuf", "grpc++", "libgrpc", "gpr", "upb"]

        # TODO: add optional plugin components? Can we add components for executables? (all plugins mainly)
