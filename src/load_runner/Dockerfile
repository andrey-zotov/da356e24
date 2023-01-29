FROM python:3.10

RUN python -m pip install poetry
RUN poetry config virtualenvs.create false

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /usr/src/load_runner
COPY pyproject.toml .
COPY poetry.lock .

RUN poetry install --without dev --no-root

COPY . .

CMD locust --web-port 80 --users 50 --spawn-rate 2 --host "${MOVIE_SERVER_URL}" --autostart --run-time 1m
