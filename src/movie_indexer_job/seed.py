"""
Create S3 buckets and seed with data
"""
import logging

import boto3
from botocore.exceptions import ClientError

from indexer.config import AWS_ENDPOINT_URL, AWS_REGION, AWS_INBOX_BUCKET_NAME, AWS_ARCHIVE_BUCKET_NAME, AWS_STORAGE_BUCKET_NAME


def create_buckets():

    def try_create_bucket(client, bucket):
        try:
            client.create_bucket(Bucket=bucket, CreateBucketConfiguration={"LocationConstraint": AWS_REGION})
        except ClientError as e:
            if e.response['Error'].get('Code') == 'BucketAlreadyOwnedByYou':  # ignoring bucket already exists error
                pass
            else:
                raise e

    client = boto3.client("s3", endpoint_url=AWS_ENDPOINT_URL)
    try_create_bucket(client, AWS_INBOX_BUCKET_NAME)
    try_create_bucket(client, AWS_STORAGE_BUCKET_NAME)
    try_create_bucket(client, AWS_ARCHIVE_BUCKET_NAME)


def seed_inbox():
    client = boto3.client("s3", endpoint_url=AWS_ENDPOINT_URL)
    client.upload_file('data/seed_data.json', AWS_INBOX_BUCKET_NAME, 'increment1.json')


def seed_db():
    client = boto3.client("s3", endpoint_url=AWS_ENDPOINT_URL)
    client.upload_file('data/seed_data.json', AWS_STORAGE_BUCKET_NAME, 'db.json')


def main():
    logging.info("Creating buckets...")
    create_buckets()
    logging.info("Seeding db...")
    seed_db()
    logging.info("Seeding inbox...")
    seed_inbox()


if __name__ == "__main__":
    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    main()

