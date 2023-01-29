"""
Basic function timing to output
"""
import functools
import time
from dataclasses import dataclass
from typing import Dict


@dataclass
class PerfCounters:
    request_counts: Dict[str, int]
    elapsed_sum: Dict[str, float]
    avg_request_time: Dict[str, float]

    def increment(self, key: str, elapsed: float):
        print(f'Call {key}: {elapsed*1000:.1f}ms')
        if key not in self.request_counts:
            self.request_counts[key] = 0
            self.elapsed_sum[key] = 0.
        perf_counters.request_counts[key] += 1
        perf_counters.elapsed_sum[key] += elapsed
        perf_counters.avg_request_time[key] = perf_counters.elapsed_sum[key] / perf_counters.request_counts[key]


perf_counters = PerfCounters({}, {}, {})


def measure_time_elapsed(func):
    @functools.wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        key = func.__name__
        perf_counters.increment(key, total_time)
        return result
    return timeit_wrapper
