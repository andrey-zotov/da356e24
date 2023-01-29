import time
from fastapi import FastAPI, Request

from movies.search_service import SearchService


app = FastAPI()

search_service = SearchService("data-full.json")


@app.get("/")
async def root(title_contains: str = "", year: int = 0, cast: str = "", genre: str = "", page: int = 0, page_size: int = 10):

    movies = search_service.cached_find_movies(title_contains=title_contains, year=year, cast=cast, genre=genre, page=page, page_size=page_size)

    return movies


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    end_time = time.perf_counter()
    total_time = end_time - start_time
    print(f'HTTP request: {total_time * 1000:.1f}ms')
    return response

