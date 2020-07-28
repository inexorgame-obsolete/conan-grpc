from conans import ConanFile, CMake, tools
from conans.errors import ConanInvalidConfiguration
from conans.tools import Version
import os


class grpcConan(ConanFile):
    name = "grpc"
    version = "1.27.3"
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
        # "shared": [True, False],
        "fPIC": [True, False],
        "build_codegen": [True, False],
        "build_csharp_ext": [True, False]
    }
    default_options = {
        "fPIC": True,
        "build_codegen": True,
        "build_csharp_ext": False
    }

    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    requires = (
        "zlib/1.2.11",
        "openssl/1.1.1g",
        "protobuf/3.11.4",
        # "protobuf/3.9.1@bincrafters/stable",
        # "protoc_installer/3.9.1@bincrafters/stable",
        "c-ares/1.15.0",
        "abseil/20200205"
    )

    def configure(self):
        if self.settings.os == "Windows" and self.settings.compiler == "Visual Studio":
            del self.options.fPIC
            compiler_version = tools.Version(self.settings.compiler.version)
            if compiler_version < 14:
                raise ConanInvalidConfiguration("gRPC can only be built with Visual Studio 2015 or higher.")

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self._source_subfolder)

        cmake_path = os.path.join(self._source_subfolder, "CMakeLists.txt")

        # See #5
        # tools.replace_in_file(cmake_path, "_gRPC_PROTOBUF_LIBRARIES", "CONAN_LIBS_PROTOBUF")

        # Workaround until https://github.com/conan-io/conan-center-index/issues/1697 is fixed
        tools.replace_in_file(cmake_path, "absl::strings", "absl::absl")
        tools.replace_in_file(cmake_path, "absl::optional", "absl::absl")
        tools.replace_in_file(cmake_path, "absl::inlined_vector", "absl::absl")

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
        cmake.definitions['gRPC_BUILD_TESTS'] = "OFF"

        # We need the generated cmake/ files (bc they depend on the list of targets, which is dynamic)
        cmake.definitions['gRPC_INSTALL'] = "ON"
        # cmake.definitions['CMAKE_INSTALL_PREFIX'] = self._build_subfolder

        # tell grpc to use the find_package versions
        cmake.definitions['gRPC_ABSL_PROVIDER'] = "package"
        cmake.definitions['gRPC_CARES_PROVIDER'] = "package"
        cmake.definitions['gRPC_ZLIB_PROVIDER'] = "package"
        cmake.definitions['gRPC_SSL_PROVIDER'] = "package"
        cmake.definitions['gRPC_PROTOBUF_PROVIDER'] = "package"

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

        tools.rmdir(os.path.join(self.package_folder, "lib", "cmake"))
        tools.rmdir(os.path.join(self.package_folder, "lib", "pkgconfig"))
        tools.rmdir(os.path.join(self.package_folder, "share"))
    
    def package_info(self):
        self.env_info.PATH.append(os.path.join(self.package_folder, "bin"))

        self.cpp_info.names["cmake_find_package"] = "gRPC"
        self.cpp_info.names["cmake_find_package_multi"] = "gRPC"

        # self.cpp_info.libs = [
            # "grpc++_unsecure",
            # "grpc++_reflection",
            # "grpc++_error_details",
            # "grpc++",
            # "grpc_unsecure",
            # "grpc_plugin_support",
            # "grpc_cronet",
            # "grpcpp_channelz",
            # "grpc",
            # "gpr",
            # "address_sorting",
            # "upb",
        # ]

        _gRPC_ALLTARGETS_LIBRARIES = []
        _gRPC_BASELIB_LIBRARIES = []
        _gRPC_LIBRARY_PREFIX = ""

        if self.settings.os == "Linux":
            _gRPC_ALLTARGETS_LIBRARIES.extend(["dl", "rt", "m", "pthread"])
            _gRPC_LIBRARY_PREFIX = "lib"
        if tools.is_apple_os(self.settings.os):
            _gRPC_ALLTARGETS_LIBRARIES.extend(["m", "pthread"])
        if self.settings.os == "Android":
            _gRPC_ALLTARGETS_LIBRARIES.extend(["m"])
        if self.settings.os == "Windows":
            _gRPC_BASELIB_LIBRARIES.extend(["wsock32", "ws2_32", "crypt32"])


        self.cpp_info.components["upb"].libs = [_gRPC_LIBRARY_PREFIX + "upb"]

        self.cpp_info.components["address_sorting"].libs = [_gRPC_LIBRARY_PREFIX + "address_sorting"]
        self.cpp_info.components["address_sorting"].system_libs.extend(_gRPC_BASELIB_LIBRARIES + _gRPC_ALLTARGETS_LIBRARIES)
        
        self.cpp_info.components["gpr"].libs = [_gRPC_LIBRARY_PREFIX + "gpr"]
        self.cpp_info.components["gpr"].system_libs = [_gRPC_ALLTARGETS_LIBRARIES]
        if self.settings.os == "Android":
            self.cpp_info.components["gpr"].system_libs.extend(["android", "log"])
        # self.cpp_info.components["gpr"].requires = ["absl::time", "absl::strings", "absl::str_format", "absl::memory"]
        self.cpp_info.components["gpr"].requires = ["abseil::abseil"]

        self.cpp_info.components["gprc_only"].name = "grpc"
        self.cpp_info.components["gprc_only"].libs = [_gRPC_LIBRARY_PREFIX + "gprc"]
        self.cpp_info.components["grpc_only"].system_libs.extend(_gRPC_BASELIB_LIBRARIES + _gRPC_ALLTARGETS_LIBRARIES)
        if tools.is_apple_os(self.settings.os):
            self.cpp_info.components["grpc_only"].frameworks = ["CoreFoundation"]
        # self.cpp_info.components["grpc_only"].requires = ["openssl::ssl", "openssl::crypto", "zlib::zlib", "c-ares::cares", "gpr", "address_sorting", "upb", "absl::optional", "absl::string", "absl::inline_vector"]
        self.cpp_info.components["grpc_only"].requires = ["openssl::ssl", "openssl::crypto", "zlib::zlib", "c-ares::cares", "gpr", "address_sorting", "upb", "abseil::abseil"]

        self.cpp_info.components["gprc_unsecure"].libs = [_gRPC_LIBRARY_PREFIX + "gprc_unsecure"]
        self.cpp_info.components["gprc_unsecure"].system_libs.extend(_gRPC_BASELIB_LIBRARIES + _gRPC_ALLTARGETS_LIBRARIES)
        if tools.is_apple_os(self.settings.os):
            self.cpp_info.components["gprc_unsecure"].frameworks = ["CoreFoundation"]
        # self.cpp_info.components["gprc_unsecure"].requires = ["zlib::zlib", "c-ares::cares", "address_sorting" "upb", "gpr", "absl::optional", "absl::string", "absl::inline_vector"]
        self.cpp_info.components["gprc_unsecure"].requires = ["zlib::zlib", "c-ares::cares", "address_sorting", "upb", "gpr", "abseil::abseil"]

        self.cpp_info.components["grpc++"].libs = [_gRPC_LIBRARY_PREFIX + "gprc++"]
        self.cpp_info.components["grpc++"].system_libs.extend(_gRPC_BASELIB_LIBRARIES + _gRPC_ALLTARGETS_LIBRARIES)
        self.cpp_info.components["grpc++"].requires = ["openssl::ssl", "openssl::crypto", "protobuf::libprotobuf", "grpc_only", "gpr", "upb"]

        self.cpp_info.components["grpc_unsecure"].libs = [_gRPC_LIBRARY_PREFIX + "gprc_unsecure"]
        self.cpp_info.components["grpc_unsecure"].system_libs.extend(_gRPC_BASELIB_LIBRARIES + _gRPC_ALLTARGETS_LIBRARIES)
        self.cpp_info.components["grpc_unsecure"].requires = ["zlib::zlib", "c-ares::cares", "address_sorting", "upb", "gpr"]

        self.cpp_info.components["grpc++_unsecure"].libs = [_gRPC_LIBRARY_PREFIX + "gprc++_unsecure"]
        self.cpp_info.components["grpc++_unsecure"].system_libs.extend(_gRPC_BASELIB_LIBRARIES + _gRPC_ALLTARGETS_LIBRARIES)
        self.cpp_info.components["grpc++_unsecure"].requires = ["protobuf::libprotobuf", "gpr", "grpc_unsecure", "upb"]

        self.cpp_info.components["grpcpp_channelz"].libs = [_gRPC_LIBRARY_PREFIX + "grpcpp_channelz"]
        self.cpp_info.components["grpcpp_channelz"].system_libs = [_gRPC_ALLTARGETS_LIBRARIES]
        self.cpp_info.components["grpcpp_channelz"].requires = ["protobuf::libprotobuf", "grpc++", "grpc_only"]

        self.cpp_info.components["gprc_cronet"].libs = [_gRPC_LIBRARY_PREFIX + "gprc_cronet"]
        self.cpp_info.components["gprc_cronet"].system_libs.extend(_gRPC_BASELIB_LIBRARIES + _gRPC_ALLTARGETS_LIBRARIES)
        if tools.is_apple_os(self.settings.os):
            self.cpp_info.components["gprc_cronet"].frameworks = ["CoreFoundation"]
        self.cpp_info.components["gprc_cronet"].requires = ["openssl::ssl", "openssl::crypto", "zlib::zlib", "c-ares::cares", "address_sorting", "upb", "gpr"]

        self.cpp_info.components["gprc_plugin_support"].libs = [_gRPC_LIBRARY_PREFIX + "gprc_plugin_support"]
        self.cpp_info.components["gprc_plugin_support"].system_libs = [_gRPC_ALLTARGETS_LIBRARIES]
        self.cpp_info.components["gprc_plugin_support"].requires = ["protobuf::protoc", "protobuf::libprotobuf"]

        self.cpp_info.components["grpc++_error_details"].libs = [_gRPC_LIBRARY_PREFIX + "grpc++_error_details"]
        self.cpp_info.components["grpc++_error_details"].system_libs.extend(_gRPC_BASELIB_LIBRARIES + _gRPC_ALLTARGETS_LIBRARIES)
        self.cpp_info.components["grpc++_error_details"].requires = ["grpc++"]

        self.cpp_info.components["grpc++_reflection"].libs = [_gRPC_LIBRARY_PREFIX + "grpc++_reflection"]
        self.cpp_info.components["grpc++_reflection"].system_libs = [_gRPC_ALLTARGETS_LIBRARIES]
        self.cpp_info.components["grpc++_reflection"].requires = ["protobuf::protoc", "grpc++", "grpc_only"]
