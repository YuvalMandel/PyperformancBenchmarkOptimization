#!/usr/bin/env python3
"""
AES-CTR encryption/decryption for flamegraph profiling (NumPy + Numba).
Runs 1000 times to produce richer samples for py-spy/perf.
"""

from parallel_numpy_crypto_flamegraph_profile import (
    do_encrypt_numpy,
    do_decrypt_numpy,
    CLEARTEXT,
    KEY,
)

# Warm up JIT compilation once on import-sized data
_ = do_encrypt_numpy(KEY, CLEARTEXT[:16], 0)


def main():
    ciphertext = do_encrypt_numpy(KEY, CLEARTEXT, 0)
    plaintext = do_decrypt_numpy(KEY, ciphertext, 0)
    if plaintext != CLEARTEXT:
        raise RuntimeError("Encryption/decryption failed!")


if __name__ == "__main__":
    for i in range(1000):
        main()
        if (i + 1) % 100 == 0:
            print("-", end="", flush=True)
    print()
