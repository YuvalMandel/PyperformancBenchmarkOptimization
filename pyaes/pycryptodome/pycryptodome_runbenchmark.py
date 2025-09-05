import pyperf
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

# ~23,000 bytes
CLEARTEXT = b"This is a test. What could possibly go wrong? " * 500
KEY = b'\xa1\xf6%\x8c\x87}_\xcd\x89dHE8\xbf\xc9,'  # 16 bytes (AES-128)
BLOCK_SIZE = 32 * 1024  # Process in 32 KB blocks

def encrypt_decrypt_block(args):
    block_data, nonce, counter_base = args

    cipher = AES.new(KEY, AES.MODE_CTR, nonce=nonce, initial_value=counter_base)
    ciphertext = cipher.encrypt(block_data)

    cipher = AES.new(KEY, AES.MODE_CTR, nonce=nonce, initial_value=counter_base)
    plaintext = cipher.decrypt(ciphertext)
    return plaintext

def parallel_encrypt_decrypt(data):
    nonce = b'\x00' * 8  # 8-byte zero nonce
    chunks = [data[i:i + BLOCK_SIZE] for i in range(0, len(data), BLOCK_SIZE)]
    # For CTR, initial_value is the block counter (in 16-byte units).
    # Each chunk starts at byte offset i * BLOCK_SIZE, so the starting counter is offset_bytes // 16.
    
    args = []
    for i, chunk in enumerate(chunks):
        offset_bytes = i * BLOCK_SIZE
        counter_base = offset_bytes // 16
        args.append((chunk, nonce, counter_base))

    results = [encrypt_decrypt_block(arg) for arg in args]
    return b''.join(results)

def bench_pycryptodome_parallel(loops):
    range_it = range(loops)
    t0 = pyperf.perf_counter()

    for _ in range_it:
        decrypted = parallel_encrypt_decrypt(CLEARTEXT)
        if decrypted != CLEARTEXT:
            raise Exception("decrypt error!")

    dt = pyperf.perf_counter() - t0
    return dt

if __name__ == "__main__":
    runner = pyperf.Runner()
    runner.metadata['description'] = "Sequential AES (CTR mode) using pycryptodome"
    runner.bench_time_func('crypto_pycryptodome_sequential', bench_pycryptodome_parallel)


