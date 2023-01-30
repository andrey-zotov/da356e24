import json
import os
import boto3
import pytest
from moto import mock_s3

from app.config import AWS_REGION, AWS_STORAGE_BUCKET_NAME
from movies.search_service import SearchService


def get_s3_client():
    # can't be a fixture, as moto destroys state on exit
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = AWS_REGION
    os.environ["AWS_SHARED_CREDENTIALS_FILE"] = "dummy"

    client = boto3.client("s3", region_name=AWS_REGION)
    client.create_bucket(Bucket=AWS_STORAGE_BUCKET_NAME, CreateBucketConfiguration={"LocationConstraint": AWS_REGION})

    return client

def create_main_db(client):
    client.put_object(Body=b"""[
      {
        "title": "The Old Man & the Gun",
        "year": 2018,
        "cast": [
          "Robert Redford",
          "Casey Affleck",
          "Danny Glover",
          "Tika Sumpter",
          "Sissy Spacek"
        ],
        "genres": [
          "Action",
          "Thriller"
        ]
      },
      {
        "title": "Power of the Air",
        "year": 2018,
        "cast": [
          "Nicholas X. Parsons",
          "Patty Duke",
          "Michael Gross",
          "Tracy Goode",
          "Karyn Williams",
          "Wendell Kinney",
          "Veryl Jones"
        ],
        "genres": [
          "Drama"
        ]
      },
      {
        "title": "Venom",
        "year": 2018,
        "cast": [
          "Tom Hardy",
          "Michelle Williams",
          "Riz Ahmed",
          "Scott Haze",
          "Reid Scott",
          "Jenny Slate"
        ],
        "genres": [
          "Superhero",
          "Horror",
          "Action",
          "Science Fiction",
          "Thriller"
        ]
      }
    ]""", Bucket=AWS_STORAGE_BUCKET_NAME, Key="main")


@pytest.fixture
@mock_s3
def svc():
    s3 = get_s3_client()
    create_main_db(s3)
    return SearchService(s3)


def test_can_load_movies_list(svc):
    data = svc.movies_list

    assert len(data) == 3
    assert data[0].title == "The Old Man & the Gun"
    assert data[0].title_normalized == "the old man & the gun"
    assert data[0].year == 2018
    assert "Robert Redford" in data[0].cast
    assert "Thriller" in data[0].genres


def test_can_find_movies(svc):
    response = svc.find_movies(title_contains="Venom", year=0, cast="", genre="", page=0, page_size=10)
    data = response.items

    assert len(data) == 1
    assert data[0].title == "Venom"
    assert data[0].year == 2018
    assert "Scott Haze" in data[0].cast
    assert "Action" in data[0].genres


@mock_s3
def test_can_find_movies_by_normalized_title(svc):
    response = svc.find_movies(title_contains="the", year=0, cast="", genre="", page=0, page_size=10)
    data = response.items

    assert len(data) == 2


@mock_s3
def test_can_find_movies_by_all_filters(svc):
    response = svc.find_movies(title_contains="Venom", year=2018, cast="Scott Haze", genre="Action", page=0, page_size=10)
    data = response.items

    assert len(data) == 1


@mock_s3
def test_can_find_movies_with_more_pages(svc):
    response = svc.find_movies(title_contains="e", year=0, cast="", genre="", page=0, page_size=1)

    assert response.page == 0
    assert response.size == 1
    assert response.has_more

    data = response.items

    assert len(data) == 1


@mock_s3
def test_can_find_movies_with_no_more_pages(svc):
    response = svc.find_movies(title_contains="e", year=0, cast="", genre="", page=2, page_size=1)

    assert response.page == 2
    assert response.size == 1
    assert not response.has_more

    data = response.items

    assert len(data) == 1


@mock_s3
def test_can_find_movies_with_empty_page(svc):
    response = svc.find_movies(title_contains="e", year=0, cast="", genre="", page=3, page_size=1)

    data = response.items

    assert len(data) == 0
