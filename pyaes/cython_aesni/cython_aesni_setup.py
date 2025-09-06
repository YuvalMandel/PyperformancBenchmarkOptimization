#!/usr/bin/env python3
"""
Setup script for Cython AESNI CTR implementation.
"""

from setuptools import setup, Extension
from Cython.Build import cythonize
import numpy as np

# Define the Cython extension with optimizations
extensions = [
    Extension(
        "cython_aesni",
        ["cython_aesni.pyx"],
        include_dirs=[np.get_include()],
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
    name="cython_aesni",
    ext_modules=cythonize(extensions, compiler_directives={
        'language_level': 3,
        'boundscheck': False,
        'wraparound': False,
        'cdivision': True,
        'nonecheck': False,
    }),
    zip_safe=False,
    py_modules=[],  # Don't auto-discover Python modules
    packages=[],    # Don't auto-discover packages
)
