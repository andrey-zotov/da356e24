from fastapi import FastAPI

from utils.perf_tools import PerfCounters, perf_counters

app = FastAPI()


@app.get("/perf_counters", response_model=PerfCounters)
async def get_perf_counters():
    """
    Internal - get perf counters
    """

    return perf_counters
