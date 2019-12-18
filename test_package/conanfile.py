#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, CMake, tools
import os
import threading
import time


class TestPackageConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake"

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def imports(self):
        self.copy("*", "bin", "bin")

    def test(self):
        if not tools.cross_building(self.settings):
            bin_path = os.path.join(".", "bin", "greeter_client_server")
            self.run(bin_path, run_environment=True)
