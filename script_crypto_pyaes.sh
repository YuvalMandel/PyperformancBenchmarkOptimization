# Environment setup and dependency installation
python3-dbg -m pip install --user pyperf
python3-dbg -m pip install --user pyaes
python3-dbg -m pip install --user py-spy
export PATH="/root/.local/bin:$PATH"
source /root/.bashrc
python3-dbg -m pip install --user pycryptodome
python3-dbg -m pip install --user numpy
python3-dbg -m pip install --user numba
# Benchmark execution using pyperformance and validating correctness
original_runtime=$(python3-dbg pyaes/original/run_benchmark.py \
  | awk '/Mean/ {
      if ($7 == "ms") {print $6 * 1000}
      else if ($7 == "us") {print $6}
  }')
echo "Original runtime: ${original_runtime} us"
python3-dbg pyaes/pycryptodome/pycryptodome_validate.py
pycryptodome_runtime=$(python3-dbg pyaes/pycryptodome/pycryptodome_runbenchmark.py \
  | awk '/Mean/ {
      if ($7 == "ms") {print $6 * 1000}
      else if ($7 == "us") {print $6}
  }')
echo "Pycryptodome runtime: ${pycryptodome_runtime} us"
python3-dbg pyaes/numpy_numba/numpy_numba_validate.py
numpy_numba_runtime=$(python3-dbg pyaes/numpy_numba/numpy_numba_runbenchmark.py \
  | awk '/Mean/ {
      if ($7 == "ms") {print $6 * 1000}
      else if ($7 == "us") {print $6}
  }')
echo "numpy_numba runtime: ${numpy_numba_runtime} us"

# Flame graph and performance data generation.
py-spy record -o pyaes_profile.speedscope --format speedscope --rate 300 python3-dbg pyaes/original/pyaes_flamegraph_profile.py
py-spy record -o pycryptodome_profile.speedscope --format speedscope --rate 10000 python3-dbg pyaes/pycryptodome/pycryptodome_flamegraph_profile.py
py-spy record -o numpy_numba_profile.speedscope --format speedscope --rate 300 python3-dbg pyaes/numpy_numba/numpy_numba_flamegraph_profile.py