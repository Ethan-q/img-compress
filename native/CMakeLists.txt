cmake_minimum_required(VERSION 3.20)
project(ImgcompressNative LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

find_package(Qt6 REQUIRED COMPONENTS Widgets)

set(APP_SOURCES
    src/main.cpp
    src/app/MainWindow.h
    src/app/MainWindow.cpp
    src/core/CompressController.h
    src/core/CompressController.cpp
    src/core/CompressWorker.h
    src/core/CompressWorker.cpp
    src/engine/EngineRegistry.h
    src/engine/EngineRegistry.cpp
)

if(APPLE)
    add_executable(ImgcompressNative MACOSX_BUNDLE ${APP_SOURCES})
    set_target_properties(ImgcompressNative PROPERTIES
        MACOSX_BUNDLE_INFO_PLIST ${CMAKE_CURRENT_SOURCE_DIR}/Info.plist
    )
else()
    add_executable(ImgcompressNative ${APP_SOURCES})
endif()

target_include_directories(ImgcompressNative PRIVATE src)
target_link_libraries(ImgcompressNative PRIVATE Qt6::Widgets)
