# Environment setup and dependency installation
echo "Setting up environment"
python3-dbg -m pip install --user pyperf
python3-dbg -m pip install --user pyaes
python3-dbg -m pip install --user py-spy
export PATH="/root/.local/bin:$PATH"
source /root/.bashrc
python3-dbg -m pip install --user pycryptodome
python3-dbg -m pip install --user numpy
python3-dbg -m pip install --user numba
sudo apt-get update
sudo apt-get -y --fix-broken install
sudo apt-get dist-upgrade -y
sudo apt-get install -y \
  libexpat1=2.4.7-1ubuntu0.6 libexpat1-dev=2.4.7-1ubuntu0.6 \
  zlib1g=1:1.2.11.dfsg-2ubuntu9.2 zlib1g-dev=1:1.2.11.dfsg-2ubuntu9.2
sudo apt-mark unhold libexpat1 zlib1g
sudo apt-get -y --fix-broken install
sudo apt-get install -y python3-dev build-essential  # or python3.10-dev
python3 -m pip install -U packaging
git clone https://github.com/brendangregg/FlameGraph.git
export PATH="$PATH:$(pwd)/FlameGraph"
python3-dbg -m pip install --user cython
# Build C and cython libraries
echo "Building C and cython modules"
cd pyaes/c_aesni
rm -rf build
python3-dbg c_aesni_setup.py build_ext --inplace
cd ../../
cd pyaes/cython_aesni/
rm -rf build
python3-dbg cython_aesni_setup.py build_ext --inplace
cd ../../
# Benchmark execution using pyperformance and validating correctness
echo "Running benchmarks"
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

cd pyaes/c_aesni
python3-dbg c_aesni_validate.py
c_aesni_runtime=$(python3-dbg c_aesni_runbenchmark.py \
  | awk '/Mean/ {
      if ($7 == "ms") {print $6 * 1000}
      else if ($7 == "us") {print $6}
  }')
echo "c_aesni runtime: ${c_aesni_runtime} us"
cd ../../
python3-dbg pyaes/cython_aesni/cython_aesni_validate.py
cython_aesni_runtime=$(python3-dbg pyaes/cython_aesni/cython_aesni_runbenchmark.py \
  | awk '/Mean/ {
      if ($7 == "ms") {print $6 * 1000}
      else if ($7 == "us") {print $6}
  }')
echo "cython_aesni runtime: ${cython_aesni_runtime} us"

# Table header
printf "%-15s %-12s %-8s\n" "Name" "Runtime(us)" "Speedup"
printf "%-15s %-12s %-8s\n" "---------------" "-----------" "-------"
# Print base row
printf "%-15s %-12d %-8s\n" "pyaes" $original_runtime "1.00x"
# Function to compute speedup (faster = >1x)
print_row() {
    local name=$1
    local runtime=$2
    # speedup = base / runtime
    local speedup=$(awk -v b=$original_runtime -v r=$runtime 'BEGIN {printf "%.2fx", b/r}')
    # Use %s for the speedup string
    printf "%-15s %-12d %-8s\n" "$name" $runtime "$speedup"
}
# Print other implementations
print_row "pycryptodome" $pycryptodome_runtime
print_row "numpy_numba"  $numpy_numba_runtime
print_row "c_aesni"      $c_aesni_runtime
print_row "cython_aesni" $cython_aesni_runtime

# Flame graph and performance data generation.
echo "Creating speedscope and flamegraphs"
py-spy record -o pyaes_profile.speedscope --format speedscope --rate 300 python3-dbg pyaes/original/pyaes_flamegraph_profile.py
py-spy record -o pycryptodome_profile.speedscope --format speedscope --rate 10000 python3-dbg pyaes/pycryptodome/pycryptodome_flamegraph_profile.py
py-spy record -o numpy_numba_profile.speedscope --format speedscope --rate 300 python3-dbg pyaes/numpy_numba/numpy_numba_flamegraph_profile.py
cd pyaes/c_aesni
perf record -F 10000 -g --call-graph dwarf -- python3-dbg c_aesni_flamegraph_profile.py
perf script -i perf.data | stackcollapse-perf.pl > c_aesni.folded
flamegraph.pl c_aesni.folded > ../../c_aesni.svg
cd ../../
perf record -F 10000 -g --call-graph dwarf -- python3-dbg pyaes/cython_aesni/cython_aesni_flamegraph_profile.py
perf script -i perf.data | stackcollapse-perf.pl > cython_aesni.folded
flamegraph.pl cython_aesni.folded > cython_aesni.svg