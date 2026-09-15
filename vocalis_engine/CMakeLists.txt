cmake_minimum_required(VERSION 3.20)
project(VocalisEngine VERSION 2.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Compiler warnings and options
if(MSVC)
    add_compile_options(/W4 /permissive- /Zc:__cplusplus /utf-8)
else()
    add_compile_options(-Wall -Wextra -Wpedantic -O3)
endif()

# Core Vocalis Engine Library
add_library(vocalis_core STATIC
    src/dsp/biquad.cpp
    src/dsp/spline_interpolator.cpp
    src/dsp/noise_generator.cpp
    src/dsp/stochastic_process.cpp
    src/orchestra/air_bellows.cpp
    src/orchestra/acoustic_reeds.cpp
    src/orchestra/friction_nozzles.cpp
    src/orchestra/bioacoustics.cpp
    src/orchestra/resonant_chambers.cpp
    src/orchestra/radiation_bell.cpp
    src/orchestra/conductor.cpp
    src/extipa/phoneme_map.cpp
    src/extipa/parser.cpp
    src/extipa/cursive_compounder.cpp
    src/voice/speaker_profile.cpp
)

target_include_directories(vocalis_core PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

# Standalone CLI Executable
add_executable(vocalis_cli apps/vocalis_cli.cpp)
target_link_libraries(vocalis_cli PRIVATE vocalis_core)

# Benchmark Executable
add_executable(synthesis_benchmark benchmarks/synthesis_benchmark.cpp)
target_link_libraries(synthesis_benchmark PRIVATE vocalis_core)

# Unit Test Executables
enable_testing()

add_executable(test_dsp tests/test_dsp.cpp)
target_link_libraries(test_dsp PRIVATE vocalis_core)
add_test(NAME test_dsp COMMAND test_dsp)

add_executable(test_parser tests/test_parser.cpp)
target_link_libraries(test_parser PRIVATE vocalis_core)
add_test(NAME test_parser COMMAND test_parser)

add_executable(test_coarticulation tests/test_coarticulation.cpp)
target_link_libraries(test_coarticulation PRIVATE vocalis_core)
add_test(NAME test_coarticulation COMMAND test_coarticulation)
