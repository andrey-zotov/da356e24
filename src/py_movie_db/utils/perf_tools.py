"""
Basic function timing to output
"""
import functools
import time


def print_time_elapsed(func):
    @functools.wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        print(f'Call {func.__name__}: {total_time*1000:.1f}ms')
        return result
    return timeit_wrapper
