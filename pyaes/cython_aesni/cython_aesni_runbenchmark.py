#!/usr/bin/env python3
"""
Cython AESNI Hardware-Accelerated Implementation of the AES block-cipher.

Benchmark AES in CTR mode using the cython_aesni wrapper module.
"""

import pyperf
from cython_aesni_wrapper import AESModeOfOperationCTR, Counter

# 23,000 bytes
CLEARTEXT = b"This is a test. What could possibly go wrong? " * 500

# 128-bit key (16 bytes)
KEY = b'\xa1\xf6%\x8c\x87}_\xcd\x89dHE8\xbf\xc9,'

def encrypt_decrypt_cython_aesni(key, data, nonce):
    ctr = Counter(initial_value=0)
    aes = AESModeOfOperationCTR(key, ctr)
    ciphertext = aes.encrypt(data)

    ctr = Counter(initial_value=0)
    aes = AESModeOfOperationCTR(key, ctr)
    plaintext = aes.decrypt(ciphertext)

    return ciphertext, plaintext

def bench_cython_aesni(loops):
    range_it = range(loops)
    t0 = pyperf.perf_counter()

    for loops in range_it:
        aes = AESModeOfOperationCTR(KEY)
        ciphertext = aes.encrypt(CLEARTEXT)

        # need to reset IV for decryption
        aes = AESModeOfOperationCTR(KEY)
        plaintext = aes.decrypt(ciphertext)

        # explicitly destroy the AESNI object
        aes = None

    dt = pyperf.perf_counter() - t0
    if plaintext != CLEARTEXT:
        raise Exception("decrypt error!")

    return dt


if __name__ == "__main__":
    runner = pyperf.Runner()
    runner.metadata['description'] = ("Cython AESNI Hardware-Accelerated Implementation "
                                      "of the AES block-cipher")
    runner.bench_time_func('crypto_cython_aesni', bench_cython_aesni)
