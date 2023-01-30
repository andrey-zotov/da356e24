from os import environ

AWS_ENDPOINT_URL = (
    f"http://{environ.get('LOCALSTACK_SERVICE_HOST')}:{environ.get('LOCALSTACK_SERVICE_PORT')}" if environ.get('LOCALSTACK_SERVICE_HOST') else ""
) or environ.get("AWS_ENDPOINT_URL")
AWS_REGION = environ.get("AWS_DEFAULT_REGION")
AWS_INBOX_BUCKET_NAME = environ.get("AWS_INBOX_BUCKET_NAME")
AWS_STORAGE_BUCKET_NAME = environ.get("AWS_STORAGE_BUCKET_NAME")
AWS_ARCHIVE_BUCKET_NAME = environ.get("AWS_ARCHIVE_BUCKET_NAME")
