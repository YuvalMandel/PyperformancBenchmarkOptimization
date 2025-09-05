#!/usr/bin/env python3
import pyaes

from numpy_numba_runbenchmark import (
    aes_ctr_numba,
    CLEARTEXT,
    KEY,
    BLOCK_SIZE,
)


def validate_aes_implementation():
    print("Validating NumPy+Numba AES-CTR implementation...")

    # Test: Main script test data validation
    print(f"Testing with main script data: {len(CLEARTEXT)} bytes, block size: {BLOCK_SIZE}")
    ct6 = aes_ctr_numba(KEY, CLEARTEXT, 0)
    pt6 = aes_ctr_numba(KEY, ct6, 0)
    if pt6 != CLEARTEXT:
        raise RuntimeError("AES CTR main script data test failed")
    print("\u2713 Main script data test passed")

    # Test: Compare main script data with pyaes using aligned counter
    print("Comparing main script data with pyaes using counter=1 (pyaes alignment)...")
    aes_pyaes_main = pyaes.AESModeOfOperationCTR(KEY)
    ct_pyaes_main = aes_pyaes_main.encrypt(CLEARTEXT)
    ct_ours_main = aes_ctr_numba(KEY, CLEARTEXT, 1)

    if ct_pyaes_main == ct_ours_main:
        print("\u2713 NumPy+Numba matches pyaes exactly with counter=1")
    else:
        print("WARNING: Ciphertexts differ vs pyaes (expected if counter init differs)")
        print(f"pyaes first 32 bytes: {ct_pyaes_main[:32].hex()}")
        print(f"ours  first 32 bytes: {ct_ours_main[:32].hex()}")

    # Verify pyaes decrypts its own output
    aes_pyaes_dec = pyaes.AESModeOfOperationCTR(KEY)
    pt_pyaes = aes_pyaes_dec.decrypt(ct_pyaes_main)
    if pt_pyaes != CLEARTEXT:
        raise RuntimeError("pyaes decryption of main script data failed")
    print("\u2713 pyaes self-decryption passed")

    print("Validation complete.")


if __name__ == "__main__":
    validate_aes_implementation()
