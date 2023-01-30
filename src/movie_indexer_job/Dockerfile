FROM python:3.10

RUN python -m pip install poetry
RUN poetry config virtualenvs.create false

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /usr/src/movie_indexer_job
COPY pyproject.toml .
COPY poetry.lock .

RUN poetry install --without dev --no-root

COPY . .

CMD python main.py
