import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from scripts.simulate_chaos import burn_cpu, leak_memory

def test_burn_cpu_short_duration():
    # Run short 1-second test with 2 threads
    burn_cpu(duration_sec=1, num_threads=2)

def test_leak_memory_short_duration():
    # Run short 1-second test targeting 30MB
    leak_memory(duration_sec=1, target_mb=30)
