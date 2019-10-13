#!/usr/bin/env python

from conans import ConanFile,tools
from conans.errors import ConanInvalidConfiguration
import os

class ConanFileBase(ConanFile):
    name = "grpc"
    version = "1.23.0"
    description = "Google's RPC library and framework."
    topics = ("conan", "grpc", "rpc")
    url = "https://github.com/inexorgame/conan-grpc"
    homepage = "https://github.com/grpc/grpc"
    author = "Bincrafters <bincrafters@gmail.com>"
    license = "Apache-2.0"
    exports = ["LICENSE.md","conanfile_base.py"]
    exports_sources = ["CMakeLists.txt"]
    generators = "cmake"
    short_paths = True  # Otherwise some folders go out of the 260 chars path length scope rapidly (on windows)

    protobuf_version="3.9.1"

    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    def source(self):
        sha256 = "86d7552cb79ab9ba7243d86b768952df1907bacb828f5f53b8a740f716f3937b"
        tools.get("{}/archive/v{}.zip".format(self.homepage, self.version), sha256=sha256)
        extracted_dir = "grpc-" + self.version
        os.rename(extracted_dir, self._source_subfolder)

        cmake_path = os.path.join(self._source_subfolder, "CMakeLists.txt")
        # See #5
        tools.replace_in_file(cmake_path, "_gRPC_PROTOBUF_LIBRARIES", "CONAN_LIBS_PROTOBUF")
