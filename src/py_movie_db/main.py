import sys
import os
import time
from functools import wraps
from fastapi import FastAPI, Request
import json
import logging
import itertools


app = FastAPI()


# perf timing

def timeit(func):
    @wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        print(f'Call {func.__name__}: {total_time*1000:.1f}ms')
        return result
    return timeit_wrapper


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    end_time = time.perf_counter()
    total_time = end_time - start_time
    print(f'HTTP request: {total_time * 1000:.1f}ms')
    return response


# optimizations

# mem/cpu optimization - intern loaded strings
def deduplicate_strings(items):
    dct = dict()
    for k, v in items:
        if isinstance(v, list):
            dct[sys.intern(k)] = [sys.intern(s) for s in v]
        elif isinstance(v, str):
            if len(v) < 80:
                dct[sys.intern(k)] = sys.intern(v)
            else:
                dct[sys.intern(k)] = v
        else:
            dct[sys.intern(k)] = v
    return dct



@timeit
def load_file():
    with open('data-full.json', 'r', encoding="utf8") as _:
        return json.load(_, object_pairs_hook=deduplicate_strings)


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

        year = item["year"]
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


assign_ids(raw_data)
create_indices()


@timeit
def find_movie():
    keys = {_ for _ in ids_by_title.keys() if "Hell" in _}
    #keys = {"Hell Fest"}

    ids_by_key = [ids_by_title[k] for k in keys]
    ids = {_ for sublist in ids_by_key for _ in sublist}
    val = [data_by_id[k] for k in ids]
    return val


@timeit
def find_movie_max_len():
    keys_gen = (_ for _ in ids_by_title.keys() if "Hell" in _)
    keys = list(itertools.islice(keys_gen, 10))

    ids_by_key = [ids_by_title[k] for k in keys]
    ids = {_ for sublist in ids_by_key for _ in sublist}
    val = [data_by_id[k] for k in ids]
    return val



# TODO:
#  search
#  pagination


@app.get("/")
async def root():

    # @timeit
    # def amplify(i):
    #     movies = None
    #     for i in range(100):
    #         movies = find_movie_max_len()
    #     return movies

    movies = find_movie_max_len()

    return {"data": movies}
