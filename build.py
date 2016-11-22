from conan.packager import ConanMultiPackager

if __name__ == "__main__":
    builder = ConanMultiPackager(username="a_teammate", channel="testing")
    builder.add_common_builds()
    builder.run()
