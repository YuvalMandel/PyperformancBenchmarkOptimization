# cython: language_level=3
# distutils: language=c++
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True
# cython: nonecheck=False

"""
Optimized AESNI CTR implementation using Cython.
This provides the same performance as the C extension but with Cython syntax.
"""

import numpy as np
cimport numpy as np
from libc.stdint cimport uint8_t, uint32_t, uint64_t
from libc.stdlib cimport malloc, free
from libc.string cimport memcpy
from cpython.bytes cimport PyBytes_FromStringAndSize, PyBytes_AsString
from cpython.buffer cimport PyObject_GetBuffer, PyBuffer_Release, PyBUF_SIMPLE

# SSE4.2 and AES-NI intrinsics
cdef extern from "immintrin.h":
    ctypedef long long __m128i
    __m128i _mm_loadu_si128(const __m128i*)
    __m128i _mm_storeu_si128(__m128i*, __m128i)
    __m128i _mm_xor_si128(__m128i, __m128i)
    __m128i _mm_aesenc_si128(__m128i, __m128i)
    __m128i _mm_aesenclast_si128(__m128i, __m128i)
    __m128i _mm_aesdec_si128(__m128i, __m128i)
    __m128i _mm_aesdeclast_si128(__m128i, __m128i)
    __m128i _mm_aesimc_si128(__m128i)
    __m128i _mm_set_epi64x(long long, long long)
    __m128i _mm_aeskeygenassist_si128(__m128i, int)
    __m128i _mm_srli_si128(__m128i, int)
    __m128i _mm_set1_epi32(int)
    int _mm_cvtsi128_si32(__m128i)

# Constants
DEF BLOCK_SIZE = 16
DEF MAX_ROUNDS = 14



# AES state structure
cdef struct AESNI_State:
    __m128i erk[MAX_ROUNDS + 1]  # Encryption round keys
    __m128i drk[MAX_ROUNDS + 1]  # Decryption round keys
    unsigned int rounds

# CTR state structure
cdef struct AESNI_CTR_State:
    AESNI_State aes_state
    uint64_t counter

# Helper function for key expansion (exact copy from C implementation)
cdef inline uint32_t sub_rot(uint32_t w, unsigned int idx, int subType):
    cdef __m128i x, y, z
    
    x = _mm_set1_epi32(<int>w)
    y = _mm_set1_epi32(0)
    
    # Exact same switch statement as C implementation
    if idx == 1:
        y = _mm_aeskeygenassist_si128(x, 0x01)
    elif idx == 2:
        y = _mm_aeskeygenassist_si128(x, 0x02)
    elif idx == 3:
        y = _mm_aeskeygenassist_si128(x, 0x04)
    elif idx == 4:
        y = _mm_aeskeygenassist_si128(x, 0x08)
    elif idx == 5:
        y = _mm_aeskeygenassist_si128(x, 0x10)
    elif idx == 6:
        y = _mm_aeskeygenassist_si128(x, 0x20)
    elif idx == 7:
        y = _mm_aeskeygenassist_si128(x, 0x40)
    elif idx == 8:
        y = _mm_aeskeygenassist_si128(x, 0x80)
    elif idx == 9:
        y = _mm_aeskeygenassist_si128(x, 0x1b)
    elif idx == 10:
        y = _mm_aeskeygenassist_si128(x, 0x36)
    
    z = y
    if subType:
        z = _mm_srli_si128(y, 4)
    
    return <uint32_t>_mm_cvtsi128_si32(z)

# Key expansion function
cdef int expand_key(__m128i *erk, __m128i *drk, const uint8_t *key, unsigned int Nk, unsigned int Nr):
    cdef uint32_t rk[4*(14+2)]
    cdef unsigned int tot_words, i
    cdef uint32_t tmp
    
    tot_words = 4*(Nr+1)
    
    # Load initial key
    for i in range(Nk):
        # Load key in native byte order (like C implementation)
        # Use explicit byte loading to match C implementation
        rk[i] = (key[i*4] |
                 (key[i*4 + 1] << 8) |
                 (key[i*4 + 2] << 16) |
                 (key[i*4 + 3] << 24))
    
    # Generate round keys
    for i in range(Nk, tot_words):
        tmp = rk[i-1]
        if i % Nk == 0:
            tmp = sub_rot(tmp, i//Nk, 1)
        elif (i % Nk == 4) and (Nk == 8):
            tmp = sub_rot(tmp, i//Nk, 0)
        rk[i] = rk[i-Nk] ^ tmp
    
    # Store encryption round keys
    for i in range(0, tot_words, 4):
        erk[i//4] = _mm_loadu_si128(<__m128i*>&rk[i])
    
    # Generate decryption round keys
    drk[0] = erk[Nr]
    for i in range(1, Nr):
        drk[i] = _mm_aesimc_si128(erk[Nr-i])
    drk[Nr] = erk[0]
    
    return 0

# Initialize AES-CTR state
cdef AESNI_CTR_State* aesni_ctr_init(const uint8_t *key, size_t key_len, uint64_t initial_counter):
    cdef AESNI_CTR_State *state
    cdef unsigned int Nr
    
    if key_len == 16:
        Nr = 10
    elif key_len == 24:
        Nr = 12
    elif key_len == 32:
        Nr = 14
    else:
        return NULL
    
    state = <AESNI_CTR_State*>malloc(sizeof(AESNI_CTR_State))
    if not state:
        return NULL
    
    state.aes_state.rounds = Nr
    state.counter = initial_counter
    
    if expand_key(state.aes_state.erk, state.aes_state.drk, key, key_len//4, Nr) != 0:
        free(state)
        return NULL
    
    return state

# Cleanup AES-CTR state
cdef void aesni_ctr_cleanup(AESNI_CTR_State *state):
    if state:
        free(state)

# Optimized CTR mode encryption/decryption
cdef int aesni_ctr_process(AESNI_CTR_State *state, const uint8_t *in_data, uint8_t *out_data, size_t len):
    cdef size_t i
    cdef __m128i counter_block, encrypted_counter
    cdef uint64_t current_counter = state.counter
    cdef uint8_t counter_bytes[16]
    cdef uint64_t temp_counter
    cdef int j
    cdef size_t block_size
    cdef __m128i data_block, result
    cdef uint8_t *encrypted_bytes
    
    # Process data in 16-byte blocks
    for i in range(0, len, BLOCK_SIZE):
        # Create counter block (16 bytes)
        # pyaes format: little-endian counter in last 8 bytes
        for j in range(16):
            counter_bytes[j] = 0
        
        temp_counter = current_counter
        
        # Put counter in last 8 bytes, little-endian
        for j in range(8):
            counter_bytes[15-j] = <uint8_t>(temp_counter & 0xFF)
            temp_counter >>= 8
        
        counter_block = _mm_loadu_si128(<__m128i*>counter_bytes)
        
        # Encrypt the counter block
        encrypted_counter = _mm_xor_si128(counter_block, state.aes_state.erk[0])
        
        for j in range(1, state.aes_state.rounds):
            encrypted_counter = _mm_aesenc_si128(encrypted_counter, state.aes_state.erk[j])
        
        encrypted_counter = _mm_aesenclast_si128(encrypted_counter, state.aes_state.erk[state.aes_state.rounds])
        
        # XOR with data
        block_size = BLOCK_SIZE if (i + BLOCK_SIZE <= len) else (len - i)
        
        if block_size == BLOCK_SIZE:
            # Full block - use SIMD
            data_block = _mm_loadu_si128(<__m128i*>(in_data + i))
            result = _mm_xor_si128(data_block, encrypted_counter)
            _mm_storeu_si128(<__m128i*>(out_data + i), result)
        else:
            # Partial block - use scalar operations
            encrypted_bytes = <uint8_t*>&encrypted_counter
            for j in range(block_size):
                out_data[i + j] = in_data[i + j] ^ encrypted_bytes[j]
        
        current_counter += 1
    
    # Update the counter state
    state.counter = current_counter
    
    return 0

# Python wrapper class
cdef class AESModeOfOperationCTR:
    cdef AESNI_CTR_State *state
    cdef bint initialized
    
    def __init__(self, key, counter=None):
        cdef Py_buffer key_buf
        cdef uint64_t initial_counter = 0
        
        if counter is not None:
            initial_counter = counter.initial_value
        
        PyObject_GetBuffer(key, &key_buf, PyBUF_SIMPLE)
        
        self.state = aesni_ctr_init(<uint8_t*>key_buf.buf, key_buf.len, initial_counter)
        PyBuffer_Release(&key_buf)
        
        if not self.state:
            raise ValueError("Failed to initialize AES-CTR")
        
        self.initialized = True
    
    def encrypt(self, data):
        cdef Py_buffer in_buf, out_buf
        cdef int result
        
        if not self.initialized:
            raise RuntimeError("AES-CTR not initialized")
        
        PyObject_GetBuffer(data, &in_buf, PyBUF_SIMPLE)
        
        # Create output buffer
        out_data = PyBytes_FromStringAndSize(NULL, in_buf.len)
        PyObject_GetBuffer(out_data, &out_buf, PyBUF_SIMPLE)
        
        result = aesni_ctr_process(self.state, <uint8_t*>in_buf.buf, <uint8_t*>out_buf.buf, in_buf.len)
        
        PyBuffer_Release(&in_buf)
        PyBuffer_Release(&out_buf)
        
        if result != 0:
            raise RuntimeError("AES-CTR processing failed")
        
        return out_data
    
    def decrypt(self, data):
        # CTR mode: decryption is the same as encryption
        return self.encrypt(data)
    
    def __dealloc__(self):
        if self.initialized and self.state:
            aesni_ctr_cleanup(self.state)

# Counter class for compatibility with pyaes
cdef class Counter:
    cdef public uint64_t initial_value
    cdef uint64_t current_value
    
    def __init__(self, initial_value=0):
        self.initial_value = initial_value
        self.current_value = initial_value
    
    def __call__(self):
        cdef uint64_t result = self.current_value
        self.current_value += 1
        return result
    
    def reset(self):
        self.current_value = self.initial_value
