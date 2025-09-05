#include <Python.h>
#include <immintrin.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

// Error codes
#define ERR_NULL 1
#define ERR_MEMORY 2
#define ERR_KEY_SIZE 3
#define ERR_NR_ROUNDS 4
#define ERR_NOT_ENOUGH_DATA 5

// Block size
#define BLOCK_SIZE 16

// AES state structure
typedef struct {
    __m128i erk[15];  // Round keys for encryption
    __m128i drk[15];  // Round keys for decryption
    unsigned rounds;
} AESNI_State;

// CTR mode state
typedef struct {
    AESNI_State aes_state;
    uint64_t counter;
} AESNI_CTR_State;

// Helper function for key expansion
static uint32_t sub_rot(uint32_t w, unsigned idx, int subType) {
    __m128i x, y, z;
    
    x = _mm_set1_epi32((int)w);
    y = _mm_set1_epi32(0);
    
    switch (idx) {
        case 1:  y = _mm_aeskeygenassist_si128(x, 0x01); break;
        case 2:  y = _mm_aeskeygenassist_si128(x, 0x02); break;
        case 3:  y = _mm_aeskeygenassist_si128(x, 0x04); break;
        case 4:  y = _mm_aeskeygenassist_si128(x, 0x08); break;
        case 5:  y = _mm_aeskeygenassist_si128(x, 0x10); break;
        case 6:  y = _mm_aeskeygenassist_si128(x, 0x20); break;
        case 7:  y = _mm_aeskeygenassist_si128(x, 0x40); break;
        case 8:  y = _mm_aeskeygenassist_si128(x, 0x80); break;
        case 9:  y = _mm_aeskeygenassist_si128(x, 0x1b); break;
        case 10: y = _mm_aeskeygenassist_si128(x, 0x36); break;
    }
    
    z = y;
    if (subType) {
        z = _mm_srli_si128(y, 4);
    }
    return (uint32_t)_mm_cvtsi128_si32(z);
}

// Key expansion function
static int expand_key(__m128i *erk, __m128i *drk, const uint8_t *key, unsigned Nk, unsigned Nr) {
    uint32_t rk[4*(14+2)];
    unsigned tot_words, i;
    
    tot_words = 4*(Nr+1);
    
    // Load initial key
    for (i=0; i<Nk; i++) {
        rk[i] = *(uint32_t*)(key + i*4);
        // Check endianness and swap if needed
        #if __BYTE_ORDER__ == __ORDER_BIG_ENDIAN__
        rk[i] = __builtin_bswap32(rk[i]);
        #endif
    }
    
    // Generate round keys
    for (i=Nk; i<tot_words; i++) {
        uint32_t tmp = rk[i-1];
        if (i % Nk == 0) {
            tmp = sub_rot(tmp, i/Nk, 1);
        } else if ((i % Nk == 4) && (Nk == 8)) {
            tmp = sub_rot(tmp, i/Nk, 0);
        }
        rk[i] = rk[i-Nk] ^ tmp;
    }
    
    // Store encryption round keys
    for (i=0; i<tot_words; i+=4) {
        erk[i/4] = _mm_loadu_si128((__m128i*)&rk[i]);
    }
    
    // Generate decryption round keys
    drk[0] = erk[Nr];
    for (i=1; i<Nr; i++) {
        drk[i] = _mm_aesimc_si128(erk[Nr-i]);
    }
    drk[Nr] = erk[0];
    
    return 0;
}

// Initialize AES-CTR state
static AESNI_CTR_State* aesni_ctr_init(const uint8_t *key, size_t key_len, uint64_t initial_counter) {
    AESNI_CTR_State *state;
    unsigned Nr;
    
    if (key_len == 16) Nr = 10;
    else if (key_len == 24) Nr = 12;
    else if (key_len == 32) Nr = 14;
    else return NULL;
    
    state = malloc(sizeof(AESNI_CTR_State));
    if (!state) return NULL;
    
    state->aes_state.rounds = Nr;
    state->counter = initial_counter;
    
    if (expand_key(state->aes_state.erk, state->aes_state.drk, key, key_len/4, Nr) != 0) {
        free(state);
        return NULL;
    }
    
    return state;
}

// Cleanup AES-CTR state
static void aesni_ctr_cleanup(AESNI_CTR_State *state) {
    if (state) {
        free(state);
    }
}

// Optimized CTR mode encryption/decryption
static int aesni_ctr_process(AESNI_CTR_State *state, const uint8_t *in, uint8_t *out, size_t len) {
    size_t i;
    __m128i counter_block, encrypted_counter;
    uint64_t current_counter = state->counter;
    
    // Process data in 16-byte blocks
    for (i = 0; i < len; i += BLOCK_SIZE) {
        // Create counter block (16 bytes)
        // pyaes format: little-endian counter in last 8 bytes
        uint8_t counter_bytes[16] = {0};
        uint64_t temp_counter = current_counter;
        
        // Put counter in last 8 bytes, little-endian
        for (int j = 0; j < 8; j++) {
            counter_bytes[15-j] = (uint8_t)(temp_counter & 0xFF);
            temp_counter >>= 8;
        }
        
        counter_block = _mm_loadu_si128((__m128i*)counter_bytes);
        
        // Encrypt the counter block
        encrypted_counter = _mm_xor_si128(counter_block, state->aes_state.erk[0]);
        
        for (unsigned j = 1; j < state->aes_state.rounds; j++) {
            encrypted_counter = _mm_aesenc_si128(encrypted_counter, state->aes_state.erk[j]);
        }
        
        encrypted_counter = _mm_aesenclast_si128(encrypted_counter, state->aes_state.erk[state->aes_state.rounds]);
        
        // XOR with data
        size_t block_size = (i + BLOCK_SIZE <= len) ? BLOCK_SIZE : (len - i);
        if (block_size == BLOCK_SIZE) {
            // Full block - use SIMD
            __m128i data_block = _mm_loadu_si128((__m128i*)(in + i));
            __m128i result = _mm_xor_si128(data_block, encrypted_counter);
            _mm_storeu_si128((__m128i*)(out + i), result);
        } else {
            // Partial block - use scalar operations
            uint8_t *encrypted_bytes = (uint8_t*)&encrypted_counter;
            for (size_t j = 0; j < block_size; j++) {
                out[i + j] = in[i + j] ^ encrypted_bytes[j];
            }
        }
        
        current_counter++;
    }
    
    // Update the counter state
    state->counter = current_counter;
    
    return 0;
}

// Python wrapper functions
static PyObject* py_aesni_ctr_init(PyObject* self, PyObject* args) {
    Py_buffer key_buf;
    uint64_t initial_counter = 0;
    AESNI_CTR_State *state;
    
    if (!PyArg_ParseTuple(args, "y*|K", &key_buf, &initial_counter)) {
        return NULL;
    }
    
    state = aesni_ctr_init((uint8_t*)key_buf.buf, key_buf.len, initial_counter);
    if (!state) {
        PyBuffer_Release(&key_buf);
        PyErr_SetString(PyExc_ValueError, "Failed to initialize AES-CTR");
        return NULL;
    }
    
    PyBuffer_Release(&key_buf);
    return PyLong_FromVoidPtr(state);
}

static PyObject* py_aesni_ctr_process(PyObject* self, PyObject* args) {
    Py_buffer in_buf, out_buf;
    AESNI_CTR_State *state;
    PyObject *state_obj;
    int result;
    
    if (!PyArg_ParseTuple(args, "Oy*y*", &state_obj, &in_buf, &out_buf)) {
        return NULL;
    }
    
    state = (AESNI_CTR_State*)PyLong_AsVoidPtr(state_obj);
    if (!state) {
        PyBuffer_Release(&in_buf);
        PyBuffer_Release(&out_buf);
        PyErr_SetString(PyExc_ValueError, "Invalid AES-CTR state");
        return NULL;
    }
    
    result = aesni_ctr_process(state, (uint8_t*)in_buf.buf, (uint8_t*)out_buf.buf, in_buf.len);
    
    PyBuffer_Release(&in_buf);
    PyBuffer_Release(&out_buf);
    
    if (result != 0) {
        PyErr_SetString(PyExc_RuntimeError, "AES-CTR processing failed");
        return NULL;
    }
    
    Py_RETURN_NONE;
}

static PyObject* py_aesni_ctr_cleanup(PyObject* self, PyObject* args) {
    PyObject *state_obj;
    AESNI_CTR_State *state;
    
    if (!PyArg_ParseTuple(args, "O", &state_obj)) {
        return NULL;
    }
    
    state = (AESNI_CTR_State*)PyLong_AsVoidPtr(state_obj);
    if (state) {
        aesni_ctr_cleanup(state);
    }
    
    Py_RETURN_NONE;
}

// Method definitions
static PyMethodDef AESNICTRMethods[] = {
    {"init", py_aesni_ctr_init, METH_VARARGS, "Initialize AES-CTR state"},
    {"process", py_aesni_ctr_process, METH_VARARGS, "Process data with AES-CTR"},
    {"cleanup", py_aesni_ctr_cleanup, METH_VARARGS, "Cleanup AES-CTR state"},
    {NULL, NULL, 0, NULL}
};

// Module definition
static struct PyModuleDef aesni_ctr_module = {
    PyModuleDef_HEAD_INIT,
    "c_aesni",
    "Optimized AES-CTR module",
    -1,
    AESNICTRMethods
};

// Module initialization
PyMODINIT_FUNC PyInit_c_aesni(void) {
    return PyModule_Create(&aesni_ctr_module);
}
