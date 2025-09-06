#!/usr/bin/env python3
from c_aesni_wrapper import AESModeOfOperationCTR, Counter

# 23,000 bytes (same as benchmark)
CLEARTEXT = b"This is a test. What could possibly go wrong? " * 500

# 128-bit key (16 bytes)
KEY = b'\xa1\xf6%\x8c\x87}_\xcd\x89dHE8\xbf\xc9,'

def main():
    print("Starting AES encryption/decryption for flamegraph profiling (c_aesni)...")
    
    # Perform encryption
    print("Encrypting...")
    aes_encrypt = AESModeOfOperationCTR(KEY, Counter(initial_value=0))
    ciphertext = aes_encrypt.encrypt(CLEARTEXT)
    
    # Perform decryption
    print("Decrypting...")
    aes_decrypt = AESModeOfOperationCTR(KEY, Counter(initial_value=0))
    plaintext = aes_decrypt.decrypt(ciphertext)
    
    # Verify correctness
    if plaintext == CLEARTEXT:
        print("✓ Encryption/decryption successful!")
    else:
        print("✗ Encryption/decryption failed!")
    
    print("Profile complete!")

if __name__ == "__main__":
    main()
