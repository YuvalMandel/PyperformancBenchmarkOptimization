#!/usr/bin/env python3
"""
Setup script for building the optimized AES-CTR C extension.
"""

from setuptools import setup, Extension
from pathlib import Path

HERE = Path(__file__).parent.resolve()
SRC = str(HERE / "c_aesni.c")

# Define the extension
extensions = [
    Extension(
        "c_aesni",
        [SRC],
        extra_compile_args=[
            "-march=native",  # Enable all CPU features
            "-maes",          # Enable AES-NI
            "-msse4.2",       # Enable SSE4.2
            "-O3",            # High optimization
            "-fomit-frame-pointer",  # Optimize for speed
        ],
        extra_link_args=[
            "-march=native",
            "-maes",
            "-msse4.2",
        ],
    )
]

setup(
    name="c_aesni",
    ext_modules=extensions,
    packages=[],
    py_modules=[],
    zip_safe=False,
)
