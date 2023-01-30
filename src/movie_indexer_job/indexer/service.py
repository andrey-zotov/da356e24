import json
import logging
import os
from pprint import pformat
from typing import List, Dict, Tuple

import boto3

from indexer.config import AWS_INBOX_BUCKET_NAME, AWS_STORAGE_BUCKET_NAME



def read_inbox_entries(s3=None) -> List[Tuple[str, Dict]]:
    """
    Read inbox entries
    Returns list of tuples (filename, data)
    """
    if s3 is None:
        s3 = boto3.client("s3")

    s3objects = s3.list_objects_v2(Bucket=AWS_INBOX_BUCKET_NAME)['Contents']
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
    if s3 is None:
        s3 = boto3.client("s3")

    s3objects = s3.list_objects(Bucket=AWS_STORAGE_BUCKET_NAME)

    for item in s3objects.get('Contents'):
        data = s3.get_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=item.get('Key'))
        contents = data['Body'].read()
        json_str = contents.decode("utf-8")
        json_data = json.loads(json_str)
        return json_data

    return []


def update_main_db(db: List[Dict], entries: List[Tuple[str, Dict]]):

    # index
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
    if s3 is None:
        s3 = boto3.client("s3")
    s3.put_object(Body=json.dumps(db).encode(), Bucket=AWS_STORAGE_BUCKET_NAME, Key="main")
