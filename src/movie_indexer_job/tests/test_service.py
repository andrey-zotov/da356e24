import json
import os
import boto3
from moto import mock_s3

from indexer.config import AWS_REGION, AWS_INBOX_BUCKET_NAME, AWS_STORAGE_BUCKET_NAME, AWS_ARCHIVE_BUCKET_NAME
import indexer.service as svc


def get_s3_client():
    # can't be a fixture, as moto destroys state on exit
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = AWS_REGION
    os.environ["AWS_SHARED_CREDENTIALS_FILE"] = "dummy"

    client = boto3.client("s3", region_name=AWS_REGION)
    client.create_bucket(Bucket=AWS_INBOX_BUCKET_NAME, CreateBucketConfiguration={"LocationConstraint": AWS_REGION})
    client.create_bucket(Bucket=AWS_STORAGE_BUCKET_NAME, CreateBucketConfiguration={"LocationConstraint": AWS_REGION})
    client.create_bucket(Bucket=AWS_ARCHIVE_BUCKET_NAME, CreateBucketConfiguration={"LocationConstraint": AWS_REGION})

    return client


def create_inbox_entries(client):
    client.put_object(Body=b"""[
      {
        "title": "The Old Man & the Gun",
        "year": 2018,
        "cast": [
          "Robert Redford",
          "Casey Affleck",
          "Danny Glover",
          "Tika Sumpter",
          "Tom Waits",
          "Sissy Spacek"
        ],
        "genres": [
          "Action",
          "Thriller"
        ]
      }
    ]""", Bucket=AWS_INBOX_BUCKET_NAME, Key="dummy1")

    client.put_object(Body=b"""[
      {
        "title": "Hell Fest",
        "year": 2018,
        "cast": [
          "Bex Taylor-Klaus",
          "Amy Forsyth",
          "Reign Edwards",
          "Christian James",
          "Matt Mercurio",
          "Roby Attal"
        ],
        "genres": [
          "Horror"
        ]
      }
    ]""", Bucket=AWS_INBOX_BUCKET_NAME, Key="dummy2")


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


@mock_s3
def test_can_read_inbox_entries():
    s3 = get_s3_client()

    create_inbox_entries(s3)

    entries = svc.read_inbox_entries(s3)

    assert len(entries) == 2

    file1, data1 = entries[0]
    assert file1 == "dummy1"
    assert data1[0]["title"] == "The Old Man & the Gun"


@mock_s3
def test_can_read_main_db():
    s3 = get_s3_client()

    create_main_db(s3)

    db = svc.read_main_db(s3)

    assert len(db) == 3

    assert db[0]["title"] == "The Old Man & the Gun"
    assert db[1]["title"] == "Power of the Air"


@mock_s3
def test_can_write_main_db():
    s3 = get_s3_client()

    create_main_db(s3)

    db = svc.read_main_db(s3)
    db.extend(db)

    svc.write_main_db(db, s3)

    newdb = svc.read_main_db(s3)

    assert len(newdb) == 6
    assert json.dumps(db, sort_keys=True) == json.dumps(newdb, sort_keys=True)


@mock_s3
def test_can_update_main_db():
    s3 = get_s3_client()

    create_main_db(s3)
    create_inbox_entries(s3)

    db = svc.read_main_db(s3)
    entries = svc.read_inbox_entries(s3)

    svc.update_main_db(db, entries)
    svc.write_main_db(db, s3)

    newdb = svc.read_main_db(s3)

    assert len(newdb) == 4

    assert db[0]["title"] == "The Old Man & the Gun"
    assert "Tom Waits" in db[0]["cast"]
    assert db[1]["title"] == "Power of the Air"
    assert db[3]["title"] == "Hell Fest"


@mock_s3
def test_can_archive_inbox_entries():
    s3 = get_s3_client()

    create_inbox_entries(s3)

    entries = svc.read_inbox_entries(s3)

    svc.archive_inbox_entries(entries, s3)

    archive_entries = s3.list_objects_v2(Bucket=AWS_ARCHIVE_BUCKET_NAME)['Contents']
    assert len(archive_entries) == 2

    new_entries = svc.read_inbox_entries()
    assert len(new_entries) == 0
