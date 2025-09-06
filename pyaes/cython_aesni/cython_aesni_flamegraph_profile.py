from cython_aesni_wrapper import AESModeOfOperationCTR, Counter

# 23,000 bytes (same as benchmark)
CLEARTEXT = b"This is a test. What could possibly go wrong? " * 500

# 128-bit key (16 bytes)
KEY = b'\xa1\xf6%\x8c\x87}_\xcd\x89dHE8\xbf\xc9,'

def main():
    # Perform encryption
    aes_encrypt = AESModeOfOperationCTR(KEY, Counter(initial_value=0))
    ciphertext = aes_encrypt.encrypt(CLEARTEXT)
    
    # Perform decryption
    aes_decrypt = AESModeOfOperationCTR(KEY, Counter(initial_value=0))
    plaintext = aes_decrypt.decrypt(ciphertext)
    
    # Verify correctness
    if plaintext != CLEARTEXT:
        raise RuntimeError("Encryption/decryption failed!")

if __name__ == "__main__":
    # Run 1000 times for detailed profiling
    for i in range(1000):
        main()
        
        # Print dash every 100 calls
        if (i + 1) % 100 == 0:
            print("-", end="", flush=True)
    
    # New line at the end
    print()
