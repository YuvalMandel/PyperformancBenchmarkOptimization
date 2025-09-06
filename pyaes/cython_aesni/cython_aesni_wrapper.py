#!/usr/bin/env python3
"""
Python wrapper for Cython AESNI CTR implementation.
Provides the same interface as pyaes and other implementations.
"""

from cython_aesni import AESModeOfOperationCTR, Counter

# Re-export the classes for easy import
__all__ = ['AESModeOfOperationCTR', 'Counter']
