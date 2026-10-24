
cmake_minimum_required(VERSION 3.2)

set(CMAKE_CXX_STANDARD 14)

add_library(chiaki-jni SHARED
        src/main/cpp/chiaki-jni.c
        src/main/cpp/log.h
        src/main/cpp/log.c
        src/main/cpp/video-decoder.h
        src/main/cpp/video-decoder.c
        src/main/cpp/audio-decoder.h
        src/main/cpp/audio-decoder.c
        src/main/cpp/audio-output.h
        src/main/cpp/audio-output.cpp
        src/main/cpp/circular-fifo.hpp)
target_link_libraries(chiaki-jni chiaki-lib)

find_library(ANDROID_LIB_LOG log)
find_library(ANDROID_LIB_MEDIANDK mediandk)
find_library(ANDROID_LIB_ANDROID android)
target_link_libraries(chiaki-jni "${ANDROID_LIB_LOG}" "${ANDROID_LIB_MEDIANDK}" "${ANDROID_LIB_ANDROID}")

add_subdirectory(src/main/cpp/oboe)
# The bundled Oboe predates NDK r30. Keep its strict warnings but replace the
# removed/deprecated -Ofast switch with conforming -O3 optimization.
get_target_property(REMTEH_OBOE_FLAGS oboe COMPILE_OPTIONS)
list(REMOVE_ITEM REMTEH_OBOE_FLAGS -Ofast)
list(APPEND REMTEH_OBOE_FLAGS -O3)
set_property(TARGET oboe PROPERTY COMPILE_OPTIONS "${REMTEH_OBOE_FLAGS}")
# Legacy resamplers relied on a transitive assert include removed by new libc++.
target_compile_options(oboe PRIVATE -include cassert)
target_link_libraries(chiaki-jni oboe)
