cmake_minimum_required(VERSION 3.20)
project(ImgcompressNative LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

find_package(Qt6 REQUIRED COMPONENTS Widgets Svg)

set(APP_CONFIG_PATH "${CMAKE_CURRENT_SOURCE_DIR}/app_config.json")
file(READ "${APP_CONFIG_PATH}" APP_CONFIG_JSON)
string(JSON APP_NAME GET "${APP_CONFIG_JSON}" app_name)
string(JSON APP_EXECUTABLE GET "${APP_CONFIG_JSON}" app_executable)
string(JSON APP_BUNDLE_ID GET "${APP_CONFIG_JSON}" bundle_identifier)
configure_file(
    "${CMAKE_CURRENT_SOURCE_DIR}/Info.plist.in"
    "${CMAKE_CURRENT_BINARY_DIR}/Info.plist"
    @ONLY
)

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
    resources/resources.qrc
)

if(APPLE)
    add_executable(ImgcompressNative MACOSX_BUNDLE ${APP_SOURCES})
    set_target_properties(ImgcompressNative PROPERTIES
        MACOSX_BUNDLE_INFO_PLIST ${CMAKE_CURRENT_BINARY_DIR}/Info.plist
        OUTPUT_NAME "${APP_EXECUTABLE}"
    )
else()
    add_executable(ImgcompressNative WIN32 ${APP_SOURCES})
    set_target_properties(ImgcompressNative PROPERTIES
        OUTPUT_NAME "${APP_EXECUTABLE}"
    )
endif()

target_include_directories(ImgcompressNative PRIVATE src)
target_link_libraries(ImgcompressNative PRIVATE Qt6::Widgets Qt6::Svg)
target_compile_definitions(ImgcompressNative PRIVATE APP_DISPLAY_NAME="${APP_NAME}")
