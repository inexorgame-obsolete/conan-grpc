[![Download](https://api.bintray.com/packages/inexorgame/inexor-conan/grpc%3Ainexorgame/images/download.svg) ](https://bintray.com/inexorgame/inexor-conan/grpc%3Ainexorgame/_latestVersion)

## Conan package recipe for [*grpc*](https://github.com/grpc/grpc)

Google's RPC library and framework.

The packages generated with this **conanfile** can be found on [Bintray](https://bintray.com/inexorgame/inexor-conan/grpc%3Ainexorgame).


## Yes, this will eventually be merged into the Conan Center Index

No, it isn't ready just yet.

If you need a remote and are allowed to use another remote than CCI, you can add the inexorgame remote as written in this Readme.


## Issues

If you wish to report an issue or make a request for a package, please do so here:

[Issues Tracker](https://github.com/inexorgame/conan-grpc/issues)


## For Users

### Basic setup

    $ conan install grpc/1.34.1@inexorgame/stable

### Project setup

If you handle multiple dependencies in your project is better to add a *conanfile.txt*

    [requires]
    grpc/1.34.1@inexorgame/stable

    [generators]
    cmake

Complete the installation of requirements for your project running:

    $ mkdir build && cd build && conan install ..

Note: It is recommended that you run conan install from a build directory and not the root of the project directory.  This is because conan generates *conanbuildinfo* files specific to a single build configuration which by default comes from an autodetected default profile located in ~/.conan/profiles/default .  If you pass different build configuration options to conan install, it will generate different *conanbuildinfo* files.  Thus, they should not be added to the root of the project, nor committed to git.


## Build and package

The following command both runs all the steps of the conan file, and publishes the package to the local system cache.  This includes downloading dependencies from "build_requires" and "requires" , and then running the build() method.

    $ conan create . inexorgame/stable


### Available Options
| Option        | Default | Possible Values  |
| ------------- |:----------------- |:------------:|
| fPIC      | True |  [True, False] |
| build_codegen      | True |  [True, False] |
| build_csharp_ext      | False |  [True, False] |


## Add Remote

    $ conan remote add inexorgame "https://api.bintray.com/conan/inexorgame/inexor-conan"


## Conan Recipe License

NOTE: The conan recipe license applies only to the files of this recipe, which can be used to build and package grpc.
It does *not* in any way apply or is related to the actual software being packaged.

[MIT](https://github.com/inexorgame/conan-grpc/blob/stable/1.34.1/LICENSE.md)
