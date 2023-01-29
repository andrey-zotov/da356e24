import time
from fastapi import FastAPI, Request

from movies.search_service import SearchService, SearchResponse

app = FastAPI()

search_service = SearchService("data-full.json")


@app.get("/", response_model=SearchResponse)
async def search(title_contains: str = "", year: int = 0, cast: str = "", genre: str = "", page: int = 0, page_size: int = 10):
    """
    Search movies by title, year, cast and genre.
    Search parameters are combined using AND.

    - **title_contains**: filter movies containing <title_contains> substring; ignored if empty
    - **year**: filter movies from the year; ignored if 0
    - **cast**: filter movies having a cast member (full name is expected); ignored if empty
    - **genre**: filter movies which has the genre (full genre name is expected); ignored if empty
    """

    movies = search_service.cached_find_movies(title_contains=title_contains, year=year, cast=cast, genre=genre, page=page, page_size=page_size)

    return movies


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Basic request timing to output
    """
    start_time = time.perf_counter()
    response = await call_next(request)
    end_time = time.perf_counter()
    total_time = end_time - start_time
    print(f'HTTP request: {total_time * 1000:.1f}ms')
    return response
