#!/usr/bin/env python3
"""
AES encryption/decryption for flamegraph profiling using pyaes.
Runs 1000 times to generate detailed profiling data with py-spy.
"""

import pyaes

# 23,000 bytes (same as benchmark)
CLEARTEXT = b"This is a test. What could possibly go wrong? " * 500

# 128-bit key (16 bytes)
KEY = b'\xa1\xf6%\x8c\x87}_\xcd\x89dHE8\xbf\xc9,'

def main():
    # Perform encryption
    aes_encrypt = pyaes.AESModeOfOperationCTR(KEY)
    ciphertext = aes_encrypt.encrypt(CLEARTEXT)
    
    # Perform decryption
    aes_decrypt = pyaes.AESModeOfOperationCTR(KEY)
    plaintext = aes_decrypt.decrypt(ciphertext)

    aes_encrypt = None
    aes_decrypt = None
    
    # Verify correctness
    if plaintext != CLEARTEXT:
        raise RuntimeError("Encryption/decryption failed!")

if __name__ == "__main__":
    main()
    print()
