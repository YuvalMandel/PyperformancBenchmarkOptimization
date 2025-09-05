#!/usr/bin/env python3
"""
Comparison script between optimized AESNI CTR wrapper and pyaes implementations.
"""

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.resolve()))

import pyaes
from c_aesni_wrapper import AESModeOfOperationCTR, Counter

# Test data
CLEARTEXT = b"This is a test. What could possibly go wrong? " * 500  # 23,000 bytes
KEY = b'\xa1\xf6%\x8c\x87}_\xcd\x89dHE8\xbf\xc9,'  # 128-bit key

def encrypt_decrypt_pyaes(key, data, nonce):
    """Test pyaes encryption/decryption"""
    ctr = pyaes.Counter(initial_value=0)
    aes = pyaes.AESModeOfOperationCTR(key, ctr)
    ciphertext = aes.encrypt(data)

    ctr = pyaes.Counter(initial_value=0)
    aes = pyaes.AESModeOfOperationCTR(key, ctr)
    plaintext = aes.decrypt(ciphertext)

    return ciphertext, plaintext

def encrypt_decrypt_c_aesni(key, data, nonce):
    """Test optimized C AESNI wrapper encryption/decryption"""
    ctr = Counter(initial_value=0)
    aes = AESModeOfOperationCTR(key, ctr)
    ciphertext = aes.encrypt(data)

    ctr = Counter(initial_value=0)
    aes = AESModeOfOperationCTR(key, ctr)
    plaintext = aes.decrypt(ciphertext)

    return ciphertext, plaintext

def main():
    """Main comparison function"""
    print("Optimized AESNI CTR Wrapper vs pyaes Comparison")
    print("=" * 55)
    
    # Test basic functionality
    print("\nTesting basic functionality...")
    
    try:
        # Test pyaes
        pyaes_ciphertext, pyaes_plaintext = encrypt_decrypt_pyaes(KEY, CLEARTEXT, 0)
        print("✓ pyaes: Encryption/decryption successful")
        
        # Test optimized C AESNI wrapper
        aesni_ciphertext, aesni_plaintext = encrypt_decrypt_c_aesni(KEY, CLEARTEXT, 0)
        print("✓ Optimized C AESNI wrapper: Encryption/decryption successful")
        
        # Verify results match
        if pyaes_plaintext == aesni_plaintext:
            print("✓ Both implementations produce identical results")
        else:
            print("✗ Results differ between implementations")
            
        # Show some sample data for debugging
        print(f"\nOriginal data length: {len(CLEARTEXT)} bytes")
        print(f"pyaes result length: {len(pyaes_plaintext)} bytes")
        print(f"AESNI CTR result length: {len(aesni_plaintext)} bytes")
        
        if len(pyaes_plaintext) > 0 and len(aesni_plaintext) > 0:
            print(f"First 16 bytes match: {pyaes_plaintext[:16] == aesni_plaintext[:16]}")
            if len(pyaes_plaintext) >= 16 and len(aesni_plaintext) >= 16:
                print(f"pyaes first 16: {pyaes_plaintext[:16].hex()}")
                print(f"AESNI CTR first 16: {aesni_plaintext[:16].hex()}")
            
            # Check if ciphertexts match (they should be identical with same counter)
            print(f"\nCiphertexts match: {pyaes_ciphertext == aesni_ciphertext}")
            if len(pyaes_ciphertext) >= 16 and len(aesni_ciphertext) >= 16:
                print(f"pyaes ciphertext first 16: {pyaes_ciphertext[:16].hex()}")
                print(f"AESNI CTR ciphertext first 16: {aesni_ciphertext[:16].hex()}")
            
    except Exception as e:
        print(f"✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\nComparison complete!")

if __name__ == "__main__":
    main()
