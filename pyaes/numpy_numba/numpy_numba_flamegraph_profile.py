#!/usr/bin/env python3
from numpy_numba_runbenchmark import (
    aes_ctr_numba,
    CLEARTEXT,
    KEY,
)

# Warm up JIT compilation once on import-sized data
_ = aes_ctr_numba(KEY, CLEARTEXT[:16], 0)


def main():
    ciphertext = aes_ctr_numba(KEY, CLEARTEXT, 0)
    plaintext = aes_ctr_numba(KEY, ciphertext, 0)
    if plaintext != CLEARTEXT:
        raise RuntimeError("Encryption/decryption failed!")


if __name__ == "__main__":
    for i in range(1000):
        main()
        if (i + 1) % 100 == 0:
            print("-", end="", flush=True)
    print()
