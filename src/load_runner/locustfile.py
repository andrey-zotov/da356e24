import random

from english_words import get_english_words_set
from locust import HttpUser, task


class MovieDbApiUser(HttpUser):
    movie_queries = list(get_english_words_set(['web2'], lower=True))
    movie_frequent_queries = ["book", "dawn", "day", "fate", "word"]

    @task
    def get_all(self):
        self.client.get("/")
        self.client.get("/?page=1")
        self.client.get("/?page=2")

    @task
    def get_all_by_year(self):
        self.client.get("/?year=2000")
        self.client.get("/?year=2000&page=1")
        self.client.get("/?year=2000&page=2")

    @task
    def get_all_by_genre(self):
        self.client.get("/?year=2000&genre=Comedy")
        self.client.get("/?year=2000&genre=Comedy&page=1")
        self.client.get("/?year=2000&genre=Comedy&page=2")

    @task
    def get_all_by_cast(self):
        self.client.get("/?cast=Sean Connery&genre=Comedy")
        self.client.get("/?cast=Sean Connery&genre=Comedy&page=1")
        self.client.get("/?cast=Sean Connery&&genre=Comedy&page=2")

    # @task
    # def get_random_movie(self):
    #     word = random.choice(self.movie_queries)
    #     self.client.get(f"/?title_contains={word}")

    @task
    def get_movie_low_card(self):
        word = random.choice(self.movie_frequent_queries)
        self.client.get(f"/?title_contains={word}")

    @task
    def get_complex_query(self):
        word = random.choice(self.movie_frequent_queries)
        year = random.choice(list(range(1990,2010)))
        cast = random.choice(["Sean Connery", "Gillian Anderson", "Cate Blanchett", "Billy Bob Thornton"])
        genre = random.choice(["Drama", "Comedy"])
        self.client.get(f"/?title_contains={word}&year={year}&cast={cast}&genre={genre}")
