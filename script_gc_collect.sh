#!/bin/bash

# --- 1. Environment Setup and Dependency Installation ---
# This section ensures all necessary tools and dependencies are installed.

# Function to check for a command's existence
command_exists () {
  command -v "$1" >/dev/null 2>&1
}

echo "Checking for required dependencies..."

# Install pyperf if not already installed
if ! command_exists "pyperf"; then
  echo "pyperf not found. Installing..."
  pip install pyperf
fi

# Install flamegraph tools if not already installed
if ! command_exists "flamegraph.pl"; then
  echo "FlameGraph tools not found. Installing..."
  # This is a common method for Linux.
  git clone https://github.com/brendangregg/FlameGraph.git
  export PATH="$PATH:$(pwd)/FlameGraph"
fi

# Make sure the current directory is in the PATH for the script's duration
export PATH="$PATH:$(pwd)"

echo "Dependencies check complete."


# --- 2. Benchmark Execution (Pre-Optimization) ---
# This section runs the benchmark on the original code and generates data.

echo "Running pre-optimization benchmarks..."

# Capture the benchmark runtime output to a file
python3-dbg gc_collect/gc_collect.py > gc_collect_output.txt

# original perf commands for detailed profiling (uncomment as needed)
perf record -F 99 -g --call-graph dwarf -- python3-dbg gc_collect/gc_collect.py
#Generate flame graph from perf.data
perf script -i perf.data | stackcollapse-perf.pl > out.folded
flamegraph.pl out.folded > gc_collect.svg
echo "Flamegraph generated: gc_collect.svg"

perf report --inline > gc_report.txt

# further inspection using profiler
perf record -F 99 -g --call-graph dwarf -- python3-dbg gc_collect/gc_profiler.py
perf script -i perf.data | stackcollapse-perf.pl > out.folded
flamegraph.pl out.folded > gc_profiler.svg
perf report --inline > gc_profiler_rep.txt

perf record -F 99 -e L1-dcache-loads -g -- python3-dbg gc_collect/gc_profiler.py
perf report --inline > gc_profiler_L1_hit.txt
perf record -F 99 -e L1-dcache-load-misses -g -- python3-dbg gc_collect/gc_profiler.py
perf report --inline > gc_profiler_L1_miss.txt
perf record -F 99 -e dTLB-load-misses -g -- python3-dbg gc_collect/gc_profiler.py
perf report --inline > gc_profiler_tlb_miss.txt
perf record -F 99 -e dTLB-loads -g -- python3-dbg gc_collect/gc_profiler.py
perf report --inline > gc_collect_1000_tlb_hit.txt


# --- 3. Benchmark Execution (Post-Optimization) ---
# This section runs the benchmark on the optimized code.

echo "Running post-optimization benchmarks for gc_collect_opt.py..."

# Capture the benchmark runtime output to a file
python3-dbg gc_collect/gc_collect_opt.py > gc_collect_opt_output.txt

# perf commands for detailed profiling 
perf record -F 99 -g --call-graph dwarf -- python3-dbg gc_collect/gc_collect_opt.py
#Generate flame graph from perf.data
perf script -i perf.data | stackcollapse-perf.pl > out.folded
flamegraph.pl out.folded > gc_collect_opt.svg
echo "Flamegraph generated: gc_collect_opt.svg"
perf report --inline > gc_opt_report.txt

# further event inspection on profiler script
perf record -F 99 -g --call-graph dwarf -- python3-dbg gc_collect/gc_opt_profiler.py
perf script -i perf.data | stackcollapse-perf.pl > out.folded
flamegraph.pl out.folded > gc_opt_profiler.svg
perf report --inline > gc_opt_profiler.txt

perf record -F 99 -e L1-dcache-loads -g -- python3-dbg gc_collect/gc_opt_profiler.py
perf report --inline > gc_opt_profiler_L1_hit.txt
perf record -F 99 -e L1-dcache-load-misses -g -- python3-dbg gc_collect/gc_opt_profiler.py
perf report --inline > gc_opt_profiler_L1_miss.txt
perf record -F 99 -e dTLB-load-misses -g -- python3-dbg gc_collect/gc_opt_profiler.py
perf report --inline > gc_opt_profiler_tlb_miss.txt
perf record -F 99 -e dTLB-loads -g -- python3-dbg gc_collect/gc_opt_profiler.py
perf report --inline > gc_opt_profiler_tlb_hit.txt

echo "All post-optimization benchmarks complete."

# --- 4. Performance Comparison ---
# This section automatically extracts and compares the results.

# Extract mean runtime from gc_collect_output.txt (in ms)
original_time_ms=$(grep "Mean +- std dev" gc_collect_output.txt | awk '{print $6}')
if [ -z "$original_time_ms" ]; then
    echo "Could not find benchmark time in gc_collect_output.txt. Please check the file."
    exit 1
fi

# Extract mean runtime from gc_collect_opt_output.txt (in us)
optimized_time_us=$(grep "Mean +- std dev" gc_collect_opt_output.txt | awk '{print $6}')
if [ -z "$optimized_time_us" ]; then
    echo "Could not find benchmark time in gc_collect_opt_output.txt. Please check the file."
    exit 1
fi

# Convert optimized time from microseconds (us) to milliseconds (ms) for comparison
optimized_time_ms=$(bc -l <<< "scale=6; $optimized_time_us / 1000")

# Calculate the improvement percentage
improvement_percent=$(bc -l <<< "scale=2; ($original_time_ms - $optimized_time_ms) / $original_time_ms * 100")

# Print the final comparison statement, showing both units
echo "The original benchmark ran for ${original_time_ms} ms and the optimized version for ${optimized_time_us} us, a ${improvement_percent}% improvement."

echo "Benchmark process complete. Results can be found in the generated files."
