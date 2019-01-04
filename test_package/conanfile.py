#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

from conans import ConanFile, CMake
import os


class TestPackageConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake"
    requires = "protoc_installer/3.6.1@bincrafters/stable",

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def imports(self):
        self.copy("*", "bin", "bin")

    def test(self):
        bin_path = os.path.join(".", "bin", "greeter_client")
        self.run(bin_path, run_environment=True)
