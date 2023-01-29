import sys
import time
from functools import wraps
from typing import Iterable, Any, List, Dict

from fastapi import FastAPI, Request
import json
import itertools



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


class SearchService:

    # mem/cpu optimization - intern loaded strings
    @staticmethod
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

    def __init__(self, filename: str):
        self.data_by_id: Dict[int, Dict] = {}
        self.ids_by_title: Dict[str, List[int]] = {}
        self.ids_by_year: Dict[int, List[int]] = {}  # remove
        self.ids_by_cast: Dict[str, List[int]] = {}
        self.ids_by_genre: Dict[str, List[int]] = {}  # remove

        self.raw_data = self.load_file(filename)
        self.assign_ids()
        self.create_indices()

    @timeit
    def load_file(self, filename: str) -> Any:
        with open(filename, "r", encoding="utf8") as _:
            return json.load(_, object_pairs_hook=SearchService.deduplicate_strings)

    @timeit
    def assign_ids(self):
        for i, item in enumerate(self.raw_data):
            item['id'] = i

    @timeit
    def create_indices(self):

        for item in self.raw_data:
            id = item["id"]
            self.data_by_id[id] = item

            title = item["title"]
            if title in self.ids_by_title:
                self.ids_by_title[title].append(id)
            else:
                self.ids_by_title[title] = [id]

            year = item["year"]
            if year in self.ids_by_year:
                self.ids_by_year[year].append(id)
            else:
                self.ids_by_year[year] = [id]

            for cast in item["cast"]:
                if cast in self.ids_by_cast:
                    self.ids_by_cast[cast].append(id)
                else:
                    self.ids_by_cast[cast] = [id]

            for genre in item["genres"]:
                if genre in self.ids_by_genre:
                    self.ids_by_genre[genre].append(id)
                else:
                    self.ids_by_genre[genre] = [id]

    @timeit
    def find_movies(self, title: str, year: int, cast: str, genre: str) -> Iterable[object]:
        keys = {_ for _ in self.ids_by_title.keys() if title in _}

        ids_by_key = [self.ids_by_title[k] for k in keys]
        ids = {_ for sublist in ids_by_key for _ in sublist}
        res = [self.data_by_id[k] for k in ids]
        return res

    @timeit
    def find_movie_max_len(self, title: str, year: int, cast: str, genre: str) -> Iterable[object]:
        keys_gen = (_ for _ in self.ids_by_title.keys() if title in _)
        keys = list(itertools.islice(keys_gen, 10))

        ids_by_key = [self.ids_by_title[k] for k in keys]
        ids = {_ for sublist in ids_by_key for _ in sublist}
        res = [self.data_by_id[k] for k in ids]
        return res


app = FastAPI()

search_service = SearchService("data-full.json")


@app.get("/")
async def root(title: str = "", year: int = 0, cast: str = "", genre: str = "", page: int = 0, page_size: int = 10):

    movies = search_service.find_movie_max_len(title=title, year=year, cast=cast, genre=genre)

    return {"items": movies, "total": 0, "page": page, "size": page_size}


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    end_time = time.perf_counter()
    total_time = end_time - start_time
    print(f'HTTP request: {total_time * 1000:.1f}ms')
    return response


# TODO:
#  search
#  pagination
#  Cython?

