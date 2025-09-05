#!/usr/bin/env python3
import numpy as np
import pyperf
from numba import njit, prange, uint8, int64

# ---------------------------------------------------------------------------
# Parameters / Test data
# ---------------------------------------------------------------------------
CLEARTEXT = b"This is a test. What could possibly go wrong? " * 500  # ~23 KB
KEY = b'\xa1\xf6%\x8c\x87}_\xcd\x89dHE8\xbf\xc9,'                    # 16 bytes
BLOCK_SIZE = 16

# ---------------------------------------------------------------------------
# AES tables (S-box + Rcon) as uint8 numpy arrays
# ---------------------------------------------------------------------------
SBOX = np.array([
    0x63,0x7C,0x77,0x7B,0xF2,0x6B,0x6F,0xC5,0x30,0x01,0x67,0x2B,0xFE,0xD7,0xAB,0x76,
    0xCA,0x82,0xC9,0x7D,0xFA,0x59,0x47,0xF0,0xAD,0xD4,0xA2,0xAF,0x9C,0xA4,0x72,0xC0,
    0xB7,0xFD,0x93,0x26,0x36,0x3F,0xF7,0xCC,0x34,0xA5,0xE5,0xF1,0x71,0xD8,0x31,0x15,
    0x04,0xC7,0x23,0xC3,0x18,0x96,0x05,0x9A,0x07,0x12,0x80,0xE2,0xEB,0x27,0xB2,0x75,
    0x09,0x83,0x2C,0x1A,0x1B,0x6E,0x5A,0xA0,0x52,0x3B,0xD6,0xB3,0x29,0xE3,0x2F,0x84,
    0x53,0xD1,0x00,0xED,0x20,0xFC,0xB1,0x5B,0x6A,0xCB,0xBE,0x39,0x4A,0x4C,0x58,0xCF,
    0xD0,0xEF,0xAA,0xFB,0x43,0x4D,0x33,0x85,0x45,0xF9,0x02,0x7F,0x50,0x3C,0x9F,0xA8,
    0x51,0xA3,0x40,0x8F,0x92,0x9D,0x38,0xF5,0xBC,0xB6,0xDA,0x21,0x10,0xFF,0xF3,0xD2,
    0xCD,0x0C,0x13,0xEC,0x5F,0x97,0x44,0x17,0xC4,0xA7,0x7E,0x3D,0x64,0x5D,0x19,0x73,
    0x60,0x81,0x4F,0xDC,0x22,0x2A,0x90,0x88,0x46,0xEE,0xB8,0x14,0xDE,0x5E,0x0B,0xDB,
    0xE0,0x32,0x3A,0x0A,0x49,0x06,0x24,0x5C,0xC2,0xD3,0xAC,0x62,0x91,0x95,0xE4,0x79,
    0xE7,0xC8,0x37,0x6D,0x8D,0xD5,0x4E,0xA9,0x6C,0x56,0xF4,0xEA,0x65,0x7A,0xAE,0x08,
    0xBA,0x78,0x25,0x2E,0x1C,0xA6,0xB4,0xC6,0xE8,0xDD,0x74,0x1F,0x4B,0xBD,0x8B,0x8A,
    0x70,0x3E,0xB5,0x66,0x48,0x03,0xF6,0x0E,0x61,0x35,0x57,0xB9,0x86,0xC1,0x1D,0x9E,
    0xE1,0xF8,0x98,0x11,0x69,0xD9,0x8E,0x94,0x9B,0x1E,0x87,0xE9,0xCE,0x55,0x28,0xDF,
    0x8C,0xA1,0x89,0x0D,0xBF,0xE6,0x42,0x68,0x41,0x99,0x2D,0x0F,0xB0,0x54,0xBB,0x16
], dtype=np.uint8)

RCON = np.array([0x00,0x01,0x02,0x04,0x08,0x10,0x20,0x40,0x80,0x1B,0x36], dtype=np.uint8)

# ---------------------------------------------------------------------------
# Numba-accelerated AES core (AES-128)
# ---------------------------------------------------------------------------

@njit(uint8(uint8), cache=True)
def _xtime(a):
    return uint8(((a << 1) & 0xFF) ^ (0x1B if (a & 0x80) else 0x00))

@njit(uint8(uint8), cache=True)
def _mul2(a): return _xtime(a)

@njit(uint8(uint8), cache=True)
def _mul3(a): return uint8(_mul2(a) ^ a)

@njit(cache=True)
def _sub_bytes(state):
    for r in range(4):
        for c in range(4):
            state[r, c] = SBOX[state[r, c]]
    return state

@njit(cache=True)
def _shift_rows(state):
    # Row 1 left rotate by 1
    t = state[1, 0]
    state[1, 0], state[1, 1], state[1, 2], state[1, 3] = state[1, 1], state[1, 2], state[1, 3], t
    # Row 2 left rotate by 2
    t0, t1 = state[2, 0], state[2, 1]
    state[2, 0], state[2, 1], state[2, 2], state[2, 3] = state[2, 2], state[2, 3], t0, t1
    # Row 3 left rotate by 3
    t = state[3, 3]
    state[3, 3], state[3, 2], state[3, 1], state[3, 0] = state[3, 2], state[3, 1], state[3, 0], t
    return state

@njit(cache=True)
def _mix_columns(state):
    for c in range(4):
        s0 = state[0, c]; s1 = state[1, c]; s2 = state[2, c]; s3 = state[3, c]
        r0 = uint8(_mul2(s0) ^ _mul3(s1) ^ s2 ^ s3)
        r1 = uint8(s0 ^ _mul2(s1) ^ _mul3(s2) ^ s3)
        r2 = uint8(s0 ^ s1 ^ _mul2(s2) ^ _mul3(s3))
        r3 = uint8(_mul3(s0) ^ s1 ^ s2 ^ _mul2(s3))
        state[0, c], state[1, c], state[2, c], state[3, c] = r0, r1, r2, r3
    return state

@njit(cache=True)
def _add_round_key(state, round_key):
    for r in range(4):
        for c in range(4):
            state[r, c] ^= round_key[r, c]
    return state

@njit(cache=True)
def _bytes_to_state_colmajor(block16):
    st = np.empty((4,4), dtype=np.uint8)
    idx = 0
    for c in range(4):
        for r in range(4):
            st[r, c] = block16[idx]; idx += 1
    return st

@njit(cache=True)
def _state_to_bytes_colmajor(state):
    out = np.empty(16, dtype=np.uint8)
    idx = 0
    for c in range(4):
        for r in range(4):
            out[idx] = state[r, c]; idx += 1
    return out

@njit(cache=True)
def _expand_key_128(key_bytes):
    # AES-128 key expansion -> (11,4,4) round keys (column-major)
    Nk, Nb, Nr = 4, 4, 10
    w = np.empty((Nb*(Nr+1), 4), dtype=np.uint8)  # 44 words

    # copy initial key into w[0..3]
    for i in range(Nk):
        w[i, 0] = key_bytes[4*i + 0]
        w[i, 1] = key_bytes[4*i + 1]
        w[i, 2] = key_bytes[4*i + 2]
        w[i, 3] = key_bytes[4*i + 3]

    temp = np.empty(4, dtype=np.uint8)
    wi = Nk
    rconi = 1
    while wi < Nb*(Nr+1):
        temp[:] = w[wi-1]
        if wi % Nk == 0:
            # RotWord
            t0, t1, t2, t3 = temp[1], temp[2], temp[3], temp[0]
            temp[0], temp[1], temp[2], temp[3] = t0, t1, t2, t3
            # SubWord
            temp[0] = SBOX[temp[0]]
            temp[1] = SBOX[temp[1]]
            temp[2] = SBOX[temp[2]]
            temp[3] = SBOX[temp[3]]
            # Rcon
            temp[0] ^= RCON[rconi]
            rconi += 1
        w[wi, 0] = w[wi - Nk, 0] ^ temp[0]
        w[wi, 1] = w[wi - Nk, 1] ^ temp[1]
        w[wi, 2] = w[wi - Nk, 2] ^ temp[2]
        w[wi, 3] = w[wi - Nk, 3] ^ temp[3]
        wi += 1

    # pack into round keys (Nr+1, 4, 4) column-major
    round_keys = np.empty((Nr+1, 4, 4), dtype=np.uint8)
    idx = 0
    for rk in range(Nr+1):
        for c in range(4):
            round_keys[rk, 0, c] = w[idx, 0]
            round_keys[rk, 1, c] = w[idx, 1]
            round_keys[rk, 2, c] = w[idx, 2]
            round_keys[rk, 3, c] = w[idx, 3]
            idx += 1
    return round_keys

@njit(cache=True)
def _aes_encrypt_block_128(block16, round_keys):
    st = _bytes_to_state_colmajor(block16)
    st = _add_round_key(st, round_keys[0])
    for rnd in range(1, 10):
        st = _sub_bytes(st)
        st = _shift_rows(st)
        st = _mix_columns(st)
        st = _add_round_key(st, round_keys[rnd])
    st = _sub_bytes(st)
    st = _shift_rows(st)
    st = _add_round_key(st, round_keys[10])
    return _state_to_bytes_colmajor(st)

@njit(cache=True)
def _ctr_xor_all(data_view, out_view, initial_counter, round_keys):
    nbytes = data_view.size
    nblocks = (nbytes + 15) // 16
    for i in prange(nblocks):
        # build counter block: high 64 bits zero, low 64 bits = initial_counter + i (big-endian)
        cb = np.zeros(16, dtype=np.uint8)
        v = initial_counter + i
        cb[15] = uint8(v & 0xFF)
        cb[14] = uint8((v >> 8) & 0xFF)
        cb[13] = uint8((v >> 16) & 0xFF)
        cb[12] = uint8((v >> 24) & 0xFF)
        cb[11] = uint8((v >> 32) & 0xFF)
        cb[10] = uint8((v >> 40) & 0xFF)
        cb[9]  = uint8((v >> 48) & 0xFF)
        cb[8]  = uint8((v >> 56) & 0xFF)

        ks = _aes_encrypt_block_128(cb, round_keys)

        start = i * 16
        end = nbytes if (i == nblocks - 1) else (start + 16)
        k = 0
        for j in range(start, end):
            out_view[j] = data_view[j] ^ ks[k]
            k += 1

def aes_ctr_numba(key: bytes, data: bytes, initial_counter: int = 0) -> bytes:
    """Public wrapper: AES-128 CTR encryption/decryption (same op)."""
    if len(key) != 16:
        raise ValueError("AES-128 requires a 16-byte key")
    if len(data) == 0:
        return b""

    round_keys = _expand_key_128(np.frombuffer(key, dtype=np.uint8))
    data_view = np.frombuffer(data, dtype=np.uint8)
    out_view = np.empty_like(data_view)
    _ctr_xor_all(data_view, out_view, int64(initial_counter), round_keys)
    return out_view.tobytes()

# ---------------------------------------------------------------------------
# pyperf harness
# ---------------------------------------------------------------------------
def bench_aes_ctr_numba(loops: int):
    # warm-up (ensure JIT compiled) - single-block and small run
    _ = aes_ctr_numba(KEY, CLEARTEXT[:16], 0)

    t0 = pyperf.perf_counter()
    for _ in range(loops):
        ct = aes_ctr_numba(KEY, CLEARTEXT, 0)
        pt = aes_ctr_numba(KEY, ct, 0)
    dt = pyperf.perf_counter() - t0

    if pt != CLEARTEXT:
        raise RuntimeError("decrypt mismatch after benchmark")
    return dt

if __name__ == "__main__":
    # Clean performance benchmark without any prints or comparisons
    runner = pyperf.Runner()
    runner.metadata['description'] = (
        "Correct AES-128 CTR using NumPy buffers + Numba JIT"
    )
    runner.bench_time_func("crypto_aes_numba_ctr", bench_aes_ctr_numba)
