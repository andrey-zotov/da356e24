from indexer.lock import IngestionLock
import indexer.service as svc


def ingest_inbox():
    """
    Ingest new movies from inbox:
    - Place lock
    - Read inbox S3 in the order of file timestamps
    - Create/update movies in main movie json data file based on movie title/year
    - Release lock
    """

    # lock
    with IngestionLock():
        # read S3 content
        entries = svc.read_inbox_entries()

        # read main movie db
        db = svc.read_main_db()

        # read each file and create/update movie in the main db
        svc.update_main_db(db, entries)

        # write main movie db
        svc.write_main_db(db)


def main():
    ingest_inbox()


if __name__ == "__main__":
    main()
