import sys
import functools
import itertools
from os import environ

import boto3

from app.config import AWS_ENDPOINT_URL, AWS_STORAGE_BUCKET_NAME
from utils.perf_tools import measure_time_elapsed
from dataclasses import dataclass
import json
from typing import Iterable, List, Dict, Set, Optional


@dataclass
class Movie:
    id: Optional[int]
    title: str
    title_normalized: str
    year: int
    cast: Set[str]
    genres: Set[str]

    @staticmethod
    def normalize_title(title: str) -> str:
        return title.lower()

    @staticmethod
    def from_json_dict(item: Dict):
        return Movie(
            id=None,
            title=item["title"],
            title_normalized=Movie.normalize_title(item["title"]),
            year=item["year"],
            cast=set(item["cast"]),
            genres=set(item["genres"])
        )


@dataclass
class SearchResponse:
    items: List[Movie]
    page: int
    size: int
    has_more: bool


class SearchService:
    """
    Search service - loads movie json file and accept queries against it
    """

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

    def __init__(self):
        self.data_by_id: Dict[int, Movie] = {}
        self.ids_by_title: Dict[str, List[int]] = {}
        self.ids_by_year: Dict[int, List[int]] = {}  # remove
        self.ids_by_cast: Dict[str, List[int]] = {}
        self.ids_by_genre: Dict[str, List[int]] = {}  # remove

        self.movies_list = self.load_file()
        self.assign_ids()
        self.create_indices()

    @measure_time_elapsed
    def load_file(self) -> List[Movie]:
        s3 = boto3.client("s3", endpoint_url=AWS_ENDPOINT_URL)

        bucket_name = environ.get(AWS_STORAGE_BUCKET_NAME)

        s3objects = s3.list_objects(Bucket=bucket_name)
        for item in s3objects.get('Contents'):
            data = s3.get_object(Bucket=bucket_name, Key=item.get('Key'))
            contents = data['Body'].read()
            json_str = contents.decode("utf-8")
            json_data = json.loads(json_str, object_pairs_hook=SearchService.deduplicate_strings)
            return [Movie.from_json_dict(_) for _ in json_data]

        raise Exception("Unable to read data from S3")

    def assign_ids(self):
        for i, item in enumerate(self.movies_list):
            item.id = i

    @measure_time_elapsed
    def create_indices(self):

        for item in self.movies_list:
            id = item.id
            self.data_by_id[id] = item

            title = item.title
            if title in self.ids_by_title:
                self.ids_by_title[title].append(id)
            else:
                self.ids_by_title[title] = [id]

            year = item.year
            if year in self.ids_by_year:
                self.ids_by_year[year].append(id)
            else:
                self.ids_by_year[year] = [id]

            for cast in item.cast:
                if cast in self.ids_by_cast:
                    self.ids_by_cast[cast].append(id)
                else:
                    self.ids_by_cast[cast] = [id]

            for genre in item.genres:
                if genre in self.ids_by_genre:
                    self.ids_by_genre[genre].append(id)
                else:
                    self.ids_by_genre[genre] = [id]

    @measure_time_elapsed
    def find_movies_x(self, title: str, year: int, cast: str, genre: str, page: int, page_size: int) -> Iterable[Movie]:
        keys = {_ for _ in self.ids_by_title.keys() if title in _}

        ids_by_key = [self.ids_by_title[k] for k in keys]
        ids = {_ for sublist in ids_by_key for _ in sublist}
        res = [self.data_by_id[k] for k in ids]
        return res

    @measure_time_elapsed
    def find_movies(self, title_contains: str, year: int, cast: str, genre: str, page: int, page_size: int) -> SearchResponse:
        """
        Perform full scan of movies to evaluate conditions.
        Filter conditions are evaluated using AND.
        Note: Total count is not calculated, instead a flag has_more returned if more items exist.

        :params title_contains: filter movies containing <title_contains> substring; ignored if empty
        :params year: filter movies from the year; ignored if 0
        :params cast: filter movies having a cast member (full name is expected); ignored if empty
        :params genre: filter movies which has the genre (full genre name is expected); ignored if empty

        :returns: Dict with paginated result
        - items: list of movies
        - page: page number (value of page parameter)
        - page_size: page size (value of page parameter)
        - has_more: whether there are more records, page+1 has to be requested in this case if more results are needed
        """

        title_contains = Movie.normalize_title(title_contains)

        # slice data for pagination, this will stop the scan if sufficient items found
        generator = (item for item in self.movies_list
                     if (not title_contains or title_contains in item.title_normalized)
                     and (year == 0 or year == item.year)
                     and (not cast or cast in item.cast)
                     and (not genre or genre in item.genres))
        iterator = itertools.islice(generator, page*page_size, page_size+1)
        items = list(iterator)

        # flag if we have more items
        if len(items) > page_size:
            has_more = True
            items.pop()
        else:
            has_more = False

        return SearchResponse(
            items=items,
            page=page,
            size=page_size,
            has_more=has_more
        )

    @measure_time_elapsed
    @functools.lru_cache(maxsize=16384)
    def cached_find_movies(self, *args, **kwargs):
        """
        Cached version of find_movies
        """
        return self.find_movies(*args, **kwargs)
