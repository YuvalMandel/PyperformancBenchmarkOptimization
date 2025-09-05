#!/usr/bin/env python3
"""
AES-CTR encryption/decryption for flamegraph profiling using PyCryptodome (version 2 - sequential).
Runs 1000 times to generate detailed profiling data with py-spy.
"""

from Crypto.Cipher import AES

# 23,000 bytes (same as benchmark)
CLEARTEXT = b"This is a test. What could possibly go wrong? " * 500

# 128-bit key (16 bytes)
KEY = b'\xa1\xf6%\x8c\x87}_\xcd\x89dHE8\xbf\xc9,'

# CTR parameters: 8-byte nonce + 64-bit counter (little-endian by PyCryptodome)
NONCE = b"\x00" * 8
INITIAL_VALUE = 0

def main():
    # Encrypt
    cipher_enc = AES.new(KEY, AES.MODE_CTR, nonce=NONCE, initial_value=INITIAL_VALUE)
    ciphertext = cipher_enc.encrypt(CLEARTEXT)

    # Decrypt (reinitialize with same nonce and counter)
    cipher_dec = AES.new(KEY, AES.MODE_CTR, nonce=NONCE, initial_value=INITIAL_VALUE)
    plaintext = cipher_dec.decrypt(ciphertext)

    # Validate
    if plaintext != CLEARTEXT:
        raise RuntimeError("Encryption/decryption failed!")

if __name__ == "__main__":
    main()
    print()


