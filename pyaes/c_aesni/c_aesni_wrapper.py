#!/usr/bin/env python3
"""
Optimized Python wrapper for AES-CTR using hardware acceleration.
"""

import c_aesni

class Counter:
    """Counter class similar to pyaes.Counter"""
    def __init__(self, initial_value=0):
        self.value = initial_value
    
    def __call__(self):
        # Return current counter value and increment
        result = self.value
        self.value += 1
        return result

class AESModeOfOperationCTR:
    """Optimized AES-CTR mode implementation using AESNI hardware acceleration"""
    
    def __init__(self, key, counter=None):
        """
        Initialize AES-CTR mode
        
        Args:
            key: 16, 24, or 32 byte key
            counter: Counter object or initial counter value
        """
        if not isinstance(key, bytes):
            raise TypeError("Key must be bytes")
        
        if len(key) not in (16, 24, 32):
            raise ValueError("Key must be 16, 24, or 32 bytes")
        
        # Get initial counter value
        if counter is None:
            initial_counter = 0
        elif isinstance(counter, Counter):
            initial_counter = counter.value
        else:
            initial_counter = counter
        
        # Initialize AES-CTR state
        self.ctr_state = c_aesni.init(key, initial_counter)
        if not self.ctr_state:
            raise RuntimeError("Failed to initialize AES-CTR")
        
        self.key = key
    
    def encrypt(self, data):
        """
        Encrypt data using AES-CTR mode
        
        Args:
            data: Data to encrypt (bytes)
            
        Returns:
            Encrypted data (bytes)
        """
        if not isinstance(data, bytes):
            raise TypeError("Data must be bytes")
        
        if not data:
            return b''
        
        # Create output buffer
        output = bytearray(len(data))
        
        # Process data using optimized C implementation
        c_aesni.process(self.ctr_state, data, output)
        
        return bytes(output)
    
    def decrypt(self, data):
        """
        Decrypt data using AES-CTR mode
        
        Args:
            data: Data to decrypt (bytes)
            
        Returns:
            Decrypted data (bytes)
        """
        # CTR mode is symmetric, so decryption is the same as encryption
        return self.encrypt(data)
    
    def __del__(self):
        """Cleanup AES-CTR state when object is destroyed"""
        if hasattr(self, 'ctr_state') and self.ctr_state:
            try:
                c_aesni.cleanup(self.ctr_state)
            except:
                pass
