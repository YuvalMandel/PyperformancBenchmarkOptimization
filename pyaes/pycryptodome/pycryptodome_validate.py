from Crypto.Cipher import AES
import pyaes

CLEARTEXT = b"This is a test. What could possibly go wrong? " * 500  # ~23,000 bytes
KEY = b'\xa1\xf6%\x8c\x87}_\xcd\x89dHE8\xbf\xc9,'  # 128-bit key
# Use empty nonce to align with pyaes' pure 128-bit counter starting at 0
NONCE = b""

def encrypt_decrypt_pycryptodome(key, data, nonce):
    """Test PyCryptodome AES-CTR encryption/decryption."""
    cipher = AES.new(key, AES.MODE_CTR, nonce=nonce, initial_value=0)
    ciphertext = cipher.encrypt(data)

    cipher = AES.new(key, AES.MODE_CTR, nonce=nonce, initial_value=0)
    plaintext = cipher.decrypt(ciphertext)

    return ciphertext, plaintext

def encrypt_decrypt_pyaes(key, data):
    """Test pyaes AES-CTR encryption/decryption (pure counter)."""
    ctr = pyaes.Counter(initial_value=0)
    aes = pyaes.AESModeOfOperationCTR(key, ctr)
    ciphertext = aes.encrypt(data)

    ctr = pyaes.Counter(initial_value=0)
    aes = pyaes.AESModeOfOperationCTR(key, ctr)
    plaintext = aes.decrypt(ciphertext)

    return ciphertext, plaintext

def main():
    print("PyCryptodome vs pyaes AES-CTR Validation")
    print("=" * 40)

    # Test basic functionality
    print("\nTesting basic functionality...")
    try:
        # PyCryptodome
        ct_crypto, pt_crypto = encrypt_decrypt_pycryptodome(KEY, CLEARTEXT, NONCE)
        if pt_crypto != CLEARTEXT:
            raise Exception("plaintext mismatch")
        print("\u2713 PyCryptodome: Encryption/decryption successful")

        # pyaes
        ct_pyaes, pt_pyaes = encrypt_decrypt_pyaes(KEY, CLEARTEXT)
        if pt_pyaes != CLEARTEXT:
            raise Exception("pyaes plaintext mismatch")
        print("\u2713 pyaes: Encryption/decryption successful")

        # Compare results
        same_plaintext = pt_crypto == pt_pyaes == CLEARTEXT
        same_ciphertext = ct_crypto == ct_pyaes
        print(f"\nPlaintext identical across implementations: {same_plaintext}")
        print(f"Ciphertext identical across implementations: {same_ciphertext}")

        print(f"\nOriginal data length: {len(CLEARTEXT)} bytes")
        print(f"PyCryptodome ciphertext length: {len(ct_crypto)} bytes")
        print(f"pyaes ciphertext length: {len(ct_pyaes)} bytes")
        if len(pt_crypto) > 0 and len(pt_pyaes) > 0:
            print(f"First 16 bytes match: {pt_crypto[:16] == pt_pyaes[:16] == CLEARTEXT[:16]}")
            print(f"PyCryptodome first 16: {pt_crypto[:16].hex()}")
            print(f"pyaes first 16:       {pt_pyaes[:16].hex()}")

    except Exception as e:
        print(f"\u2717 Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return

if __name__ == "__main__":
    main()
