FROM python:3.10

RUN python -m pip install poetry
RUN poetry config virtualenvs.create false

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /usr/src/py_movie_db
COPY pyproject.toml .
COPY poetry.lock .

RUN poetry install --without dev --no-root

COPY . .

CMD uvicorn app.main:app --host 0.0.0.0 --port 80 --no-use-colors --reload
