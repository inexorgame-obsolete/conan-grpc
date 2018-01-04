from conans import ConanFile, CMake
import os

channel = os.getenv("CONAN_CHANNEL", "stable")
username = os.getenv("CONAN_USERNAME", "inexorgame")
package_ref = os.getenv("CONAN_REFERENCE", "gRPC/1.8.3")


class gRPCTestConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    requires = "{}@{}/{}".format(package_ref, username, channel)
    generators = "cmake"

    def build(self):
        cmake = CMake(self)
        self.run('cmake %s %s' % (self.source_folder, cmake.command_line))
        self.run("cmake --build . %s" % cmake.build_config)
#        if self.settings.os == "Macos":
 #           self.run("cd bin; for LINK_DESTINATION in $(otool -L client | grep libproto | cut -f 1 -d' '); do install_name_tool -change \"$LINK_DESTINATION\" \"@executable_path/$(basename $LINK_DESTINATION)\" client; done")

    def imports(self):
        self.copy("*", "bin", "bin")

    def test(self):
        self.run(os.path.join(".", "bin", "greeter_client"))
