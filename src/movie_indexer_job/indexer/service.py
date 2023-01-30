import datetime
import json
import logging
from typing import List, Dict, Tuple

import boto3

from indexer.config import AWS_ENDPOINT_URL, AWS_INBOX_BUCKET_NAME, AWS_STORAGE_BUCKET_NAME, AWS_ARCHIVE_BUCKET_NAME


def read_inbox_entries(s3=None) -> List[Tuple[str, Dict]]:
    """
    Read inbox entries
    Returns list of tuples (filename, data)
    """
    if s3 is None:
        s3 = boto3.client("s3", endpoint_url=AWS_ENDPOINT_URL)

    resp = s3.list_objects_v2(Bucket=AWS_INBOX_BUCKET_NAME)

    # check if empty
    if 'Contents' not in resp:
        return []

    s3objects = resp['Contents']
    keys = [obj['Key'] for obj in sorted(s3objects, key=lambda obj: int(obj['LastModified'].timestamp()))]

    res: List[Tuple[str, Dict]] = []
    for k in keys:
        data = s3.get_object(Bucket=AWS_INBOX_BUCKET_NAME, Key=k)
        contents = data['Body'].read()
        try:
            json_str = contents.decode("utf-8")
            json_data = json.loads(json_str)
            res.append((k, json_data))
        except Exception as e:
            logging.error("Can't load item with key %s: %s", k, repr(e))

    return res


def read_main_db(s3=None) -> List[Dict]:
    """
    Read main db json
    """
    if s3 is None:
        s3 = boto3.client("s3", endpoint_url=AWS_ENDPOINT_URL)

    s3objects = s3.list_objects(Bucket=AWS_STORAGE_BUCKET_NAME)

    for item in s3objects.get('Contents'):
        data = s3.get_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=item.get('Key'))
        contents = data['Body'].read()
        json_str = contents.decode("utf-8")
        json_data = json.loads(json_str)
        return json_data

    return []


def update_main_db(db: List[Dict], entries: List[Tuple[str, Dict]]):
    """
    Update main db with inbox entries
    """

    # index for most basic entity matching
    movies_by_title_year = {_["title"] + str(_["year"]): _ for _ in db}

    for entry in entries:
        file_key, items = entry
        for item in items:
            movie_key = item["title"] + str(item["year"])
            if movie_key in movies_by_title_year:
                movies_by_title_year[movie_key].clear()
                movies_by_title_year[movie_key].update(item)
            else:
                movies_by_title_year[movie_key] = item
                db.append(item)


def write_main_db(db: List[Dict], s3=None):
    """
    Write main db back to S3
    """
    if s3 is None:
        s3 = boto3.client("s3", endpoint_url=AWS_ENDPOINT_URL)
    s3.put_object(Body=json.dumps(db).encode(), Bucket=AWS_STORAGE_BUCKET_NAME, Key="main")


def archive_inbox_entries(entries: List[Tuple[str, Dict]], s3=None):
    """
    Archive inbox entries to archive bucket
    """
    if s3 is None:
        s3 = boto3.client("s3", endpoint_url=AWS_ENDPOINT_URL)
    for entry in entries:
        file_key, items = entry
        s3.put_object(Body=json.dumps(items).encode(), Bucket=AWS_ARCHIVE_BUCKET_NAME, Key=str(int(datetime.datetime.now().timestamp() * 1000000)) + file_key)
        s3.delete_object(Bucket=AWS_INBOX_BUCKET_NAME, Key=file_key)
