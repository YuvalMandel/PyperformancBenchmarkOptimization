import gc
import pyperf

# Constants for the benchmark
CYCLES = 100
LINKS = 20


class Node:
    """A simple node class for creating linked lists."""

    def __init__(self):
        self.next = None
        self.prev = None

    def link_next(self, next_node):
        """Links this node to the next one."""
        self.next = next_node
        self.next.prev = self


def create_cycle(node, n_links):
    """Create a cycle of n_links nodes, starting with node."""

    if n_links == 0:
        return

    current = node
    for i in range(n_links):
        next_node = Node()
        current.link_next(next_node)
        current = next_node

    current.link_next(node)


def create_gc_cycles(n_cycles, n_links):
    """Create n_cycles cycles n_links+1 nodes each."""

    cycles = []
    for _ in range(n_cycles):
        node = Node()
        cycles.append(node)
        create_cycle(node, n_links)
    return cycles


def benchamark_collection(loops, cycles, links):
    """
    Performs a garbage collection benchmark over multiple loops.

    Args:
        loops (int): The number of times to run the benchmark.
        cycles (int): The number of cycles to create for each run.
        links (int): The number of links per cycle.

    Returns:
        float: The total elapsed time for all runs.
    """
    total_time = 0
    for _ in range(loops):
        # Force a collection to start with a clean slate
        gc.collect()

        # Create the cycles that will be garbage collected
        all_cycles = create_gc_cycles(cycles, links)

        # Main loop to measure
        del all_cycles
        t0 = pyperf.perf_counter()
        collected = gc.collect()
        total_time += pyperf.perf_counter() - t0

        # Assert the correct number of objects were collected.
        # This check is good practice for a benchmark.
        assert collected is None or collected >= cycles * (links + 1)

    return total_time


if __name__ == "__main__":
    # The number of times to run the benchmark.
    num_runs = 1000

    print(f"Running the benchmark function {num_runs} times...")

    # Run the benchmark function directly and get the total elapsed time.
    elapsed_time = benchamark_collection(num_runs, CYCLES, LINKS)

    print(f"Total elapsed time for {num_runs} runs: {elapsed_time:.6f} seconds")
    print(f"Average time per run: {elapsed_time / num_runs:.6f} seconds")
