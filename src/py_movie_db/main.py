import os
import time
from functools import wraps
from fastapi import FastAPI, Request
import aioredis
import redis
import json
import pickle
import logging


app = FastAPI()

redis_url = os.getenv("REDIS_URL")
ards = aioredis.from_url(redis_url)  # , decode_responses=True
rds = redis.from_url(redis_url)


def timeit(func):
    @wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        print(f'Call {func.__name__}: {total_time:.4f}s')
        return result
    return timeit_wrapper


@timeit
def load_file():
    with open('data-full.json', 'r', encoding="utf8") as _:
        return json.load(_)


@timeit
def assign_ids(raw_data):
    for i, item in enumerate(raw_data):
        item['id'] = i


raw_data = load_file()
data_by_id = {}
ids_by_title = {}
ids_by_year = {}
ids_by_cast = {}
ids_by_genre = {}


@timeit
def create_indices():

    for item in raw_data:
        id = item["id"]
        data_by_id[id] = item

        title = item["title"]
        if title in ids_by_title:
            ids_by_title[title].append(id)
        else:
            ids_by_title[title] = [id]

        year = item["title"]
        if year in ids_by_year:
            ids_by_year[year].append(id)
        else:
            ids_by_year[year] = [id]

        for cast in item["cast"]:
            if cast in ids_by_cast:
                ids_by_cast[cast].append(id)
            else:
                ids_by_cast[cast] = [id]

        for genre in item["genres"]:
            if genre in ids_by_genre:
                ids_by_genre[genre].append(id)
            else:
                ids_by_genre[genre] = [id]


@timeit
def index_titles(data):
    unique_data = {_["title"] for _ in data}
    data_by_keys = {k: [_ for _ in data if _["title"] == k] for k in unique_data}
    rds.mset({k: pickle.dumps(v) for k, v in data_by_keys})

@timeit
def index_years(data):
    unique_data = {_["year"] for _ in data}
    data_by_keys = {k: [_ for _ in data if _["year"] == k] for k in unique_data}
    rds.mset({k: pickle.dumps(v) for k, v in data_by_keys})


assign_ids(raw_data)
create_indices()
# index_data()
# index_titles(mdata)


# @app.middleware("http")
# async def add_process_time_header(request: Request, call_next):
#     start_time = time.time()
#     response = await call_next(request)
#     print("Time took to process the request and return response is {} sec".format(time.time() - start_time))
#     return response
#
#

@app.get("/")
async def root():
    #val = await ards.get("Hell Fest")
    #val = pickle.loads(val)

    #ids = ids_by_title["Hell Fest"]

    #keys = {_ for _ in ids_by_title.keys() if "Hell" in _}
    keys = {"Hell Fest"}
    ids_by_key = [ids_by_title[k] for k in keys]
    ids = {_ for sublist in ids_by_key for _ in sublist}
    val = [data_by_id[k] for k in ids][0]

    return {"message": f"Hello World {val}"}
