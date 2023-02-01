FROM rust:1.67 as builder
WORKDIR /usr/src/rs_movie_db

COPY Cargo.toml .
COPY Cargo.lock .
COPY main.rs .
RUN cargo install --profile release --path .

FROM debian:bullseye-slim
RUN apt-get update && apt-get install -y libssl-dev ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=builder /usr/local/cargo/bin/rs-movie-db /usr/local/bin/rs-movie-db
CMD ["rs-movie-db"]
