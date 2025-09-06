#!/usr/bin/env python3
"""
Validation script to compare Cython AESNI CTR implementation with pyaes.
"""

import pyaes
from cython_aesni_wrapper import AESModeOfOperationCTR, Counter

# Test data
CLEARTEXT = b"This is a test. What could possibly go wrong? " * 500  # 23,000 bytes
KEY = b'\xa1\xf6%\x8c\x87}_\xcd\x89dHE8\xbf\xc9,'  # 128-bit key

def test_basic_functionality():
    """Test basic encryption/decryption functionality"""
    print("Testing basic functionality...")
    
    # Test pyaes
    try:
        ctr1 = pyaes.Counter(initial_value=0)
        aes1 = pyaes.AESModeOfOperationCTR(KEY, ctr1)
        ciphertext1 = aes1.encrypt(CLEARTEXT)
        
        ctr1 = pyaes.Counter(initial_value=0)
        aes1 = pyaes.AESModeOfOperationCTR(KEY, ctr1)
        plaintext1 = aes1.decrypt(ciphertext1)
        
        if plaintext1 == CLEARTEXT:
            print("✓ pyaes: Encryption/decryption successful")
        else:
            print("✗ pyaes: Encryption/decryption failed")
            return False
    except Exception as e:
        print(f"✗ pyaes: Error during testing: {e}")
        return False
    
    # Test Cython AESNI CTR
    try:
        ctr2 = Counter(initial_value=0)
        aes2 = AESModeOfOperationCTR(KEY, ctr2)
        ciphertext2 = aes2.encrypt(CLEARTEXT)
        
        ctr2 = Counter(initial_value=0)
        aes2 = AESModeOfOperationCTR(KEY, ctr2)
        plaintext2 = aes2.decrypt(ciphertext2)
        
        if plaintext2 == CLEARTEXT:
            print("✓ Cython AESNI CTR: Encryption/decryption successful")
        else:
            print("✗ Cython AESNI CTR: Encryption/decryption failed")
            return False
    except Exception as e:
        print(f"✗ Cython AESNI CTR: Error during testing: {e}")
        return False
    
    return True

def compare_results():
    """Compare results between pyaes and Cython AESNI CTR"""
    print("\nComparing results between implementations...")
    
    # Get results from both implementations
    ctr1 = pyaes.Counter(initial_value=0)
    aes1 = pyaes.AESModeOfOperationCTR(KEY, ctr1)
    ciphertext1 = aes1.encrypt(CLEARTEXT)
    
    ctr2 = Counter(initial_value=0)
    aes2 = AESModeOfOperationCTR(KEY, ctr2)
    ciphertext2 = aes2.encrypt(CLEARTEXT)
    
    # Compare results
    if ciphertext1 == ciphertext2:
        print("✓ Both implementations produce identical results")
        return True
    else:
        print("✗ Results differ between implementations")
        
        # Debug information
        print(f"Original data length: {len(CLEARTEXT)} bytes")
        print(f"pyaes result length: {len(ciphertext1)} bytes")
        print(f"Cython AESNI CTR result length: {len(ciphertext2)} bytes")
        
        # Compare first 16 bytes
        first_16_match = ciphertext1[:16] == ciphertext2[:16]
        print(f"First 16 bytes match: {first_16_match}")
        
        if len(ciphertext1) >= 16 and len(ciphertext2) >= 16:
            print(f"pyaes first 16: {ciphertext1[:16].hex()}")
            print(f"Cython AESNI CTR first 16: {ciphertext2[:16].hex()}")
        
        # Find first difference
        min_len = min(len(ciphertext1), len(ciphertext2))
        for i in range(min_len):
            if ciphertext1[i] != ciphertext2[i]:
                print(f"First difference at byte {i}: {ciphertext1[i]:02x} vs {ciphertext2[i]:02x}")
                break
        
        return False

def main():
    """Main validation function"""
    print("=" * 40)
    print("Cython AESNI CTR vs pyaes Validation")
    print("=" * 40)
    
    # Test basic functionality
    if not test_basic_functionality():
        print("\nBasic functionality test failed!")
        return
    
    # Compare results
    if compare_results():
        print("\n🎉 All tests passed! Cython AESNI CTR implementation is correct.")
    else:
        print("\n❌ Validation failed! Results don't match pyaes.")
    
    print("\nComparison complete!")

if __name__ == "__main__":
    main()
