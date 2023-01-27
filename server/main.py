import os
import time

from fastapi import FastAPI, Request
import aioredis
import redis
import json
import pickle


app = FastAPI()

redis_url = os.getenv("REDIS_URL")
ards = aioredis.from_url(redis_url)  # , decode_responses=True
rds = redis.from_url(redis_url)


def read_data():
    with open('data-small.json', 'r', encoding="utf8") as _:
        data = json.load(_)
    print(data[0])

    for item in data:
        rds.set(item["title"], pickle.dumps(item))


read_data()


# @app.middleware("http")
# async def add_process_time_header(request: Request, call_next):
#     start_time = time.time()
#     response = await call_next(request)
#     print("Time took to process the request and return response is {} sec".format(time.time() - start_time))
#     return response
#
#

@app.get("/")
async def root():
    val = await ards.get("Hell Fest")
    val = pickle.loads(val)

    return {"message": f"Hello World {val}"}
