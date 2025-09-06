# PyperformancBenchmarkOptimization 🚀

Final Project of the Technion course 00460882 — Improving the performance of the pyaescrypto & gc_collect.

This subfolder contains self-contained scripts to validate, benchmark, and profile multiple AES implementations (original PyAES, NumPy/Numba, PyCryptodome, C AES-NI, and Cython AES-NI)

It also has the GC collect baseline and optimized.

## Structure 🗂️
- `pyaes/` 
  - `original/`: Baseline PyAES
    - `pyaes_flamegraph_profile.py`, `run_benchmark.py`
  - `numpy_numba/`: NumPy/Numba variant
    - `numpy_numba_validate.py`, `numpy_numba_runbenchmark.py`, `numpy_numba_flamegraph_profile.py`
  - `pycryptodome/`: PyCryptodome-based variant
    - `pycryptodome_validate.py`, `pycryptodome_runbenchmark.py`, `pycryptodome_flamegraph_profile.py`
  - `c_aesni/`: C AES-NI with Python wrapper
    - `c_aesni.c`, `c_aesni_wrapper.py`, `c_aesni_setup.py`, `c_aesni_validate.py`, `c_aesni_runbenchmark.py`, `c_aesni_flamegraph_profile.py`
  - `cython_aesni/`: Cython AES-NI wrapper
    - `cython_aesni.pyx`, `cython_aesni_wrapper.py`, `cython_aesni_setup.py`, `cython_aesni_validate.py`, `cython_aesni_runbenchmark.py`, `cython_aesni_flamegraph_profile.py`
- `gc_collect/` 🗑️
  - `gc_collect.py`, `gc_collect_opt.py`, `gc_profiler.py`, `gc_opt_profiler.py`
- `script_crypto_pyaes.sh`, `script_gc_collect.sh`: automated run scripts
- `prompts_aes.txt`: AES prompt log
- `prompts_gc.txt`: GC prompt log

## Setup 🔧
Make shell scripts executable
```bash
chmod +x script_crypto_pyaes.sh
chmod +x script_gc_collect.sh
```

## General overall scripts ▶️
Runs all AES installations, builds, benchmarks, and creates speedscope/flamegraphs:
```bash
./script_crypto_pyaes.sh
```
Runs all GC collect installations, benchmarks, and creates flamegraphs and perf reports:
```bash
./script_gc_collect.sh
```

## AES implementations: Generally, how to build and validate 🧮

- Original PyAES baseline:
```bash
python3-dbg pyaes/original/run_benchmark.py
```

- PyCryptodome variant:
```bash
python3-dbg pyaes/pycryptodome/pycryptodome_validate.py
python3-dbg pyaes/pycryptodome/pycryptodome_runbenchmark.py
```

- NumPy/Numba variant:
```bash
python3-dbg pyaes/numpy_numba/numpy_numba_validate.py
python3-dbg pyaes/numpy_numba/numpy_numba_runbenchmark.py
```

- C AES-NI (pyaes/c_aesni):
```bash
cd pyaes/c_aesni
python3-dbg ../../..//setup_aesni_wrapper.py build_ext --inplace
python3-dbg c_aesni_setup.py build_ext --inplace
cd -
```
Validate and benchmark:
```bash
python3-dbg pyaes/c_aesni/c_aesni_validate.py
python3-dbg pyaes/c_aesni/c_aesni_runbenchmark.py
```

- Cython AES-NI (pyaes/cython_aesni):
```bash
cd pyaes/cython_aesni
python3-dbg cython_aesni_setup.py build_ext --inplace
cd -
```
Validate and benchmark:
```bash
python3-dbg pyaes/cython_aesni/cython_aesni_validate.py
python3-dbg pyaes/cython_aesni/cython_aesni_runbenchmark.py
```

## GC implementations: Generally, how to run and profile 🗑️
Run the GC scripts and profilers:
```bash
python3-dbg gc_collect/gc_collect.py
python3-dbg gc_collect/gc_collect_opt.py
python3-dbg gc_collect/gc_profiler.py
python3-dbg gc_collect/gc_opt_profiler.py
```
