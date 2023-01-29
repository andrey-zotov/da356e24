include .env.dev
export

local-start-server:
	cd src/py_movie_db && uvicorn main:app --reload --port 8100 --no-use-colors

awslocal-create-bucket:
	-awslocal --endpoint-url=http://host.docker.internal:4567 s3api create-bucket --bucket $(AWS_STORAGE_BUCKET_NAME) --create-bucket-configuration "{\"LocationConstraint\": \"$(AWS_DEFAULT_REGION)\"}"

dc-build-indexer:
	docker-compose --profile indexer build

dc-build-server:
	docker-compose --profile server build

dc-build: dc-build-indexer dc-build-server

local-start: dc-build awslocal-create-bucket
	docker-compose --profile server --profile indexer up

local-start-infra:
	-docker-compose -f local-infra.yml -p movie-dev-infra up
