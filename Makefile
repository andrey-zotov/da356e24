include .env.dev
export

local-start-server:
	cd src/py_movie_db && uvicorn app.main:app --reload --port 8100 --no-use-colors

awslocal-create-bucket:
	-awslocal --endpoint-url=http://host.docker.internal:4567 s3api create-bucket --bucket $(AWS_STORAGE_BUCKET_NAME) --create-bucket-configuration "{\"LocationConstraint\": \"$(AWS_DEFAULT_REGION)\"}"

awslocal-upload-data:
	awslocal --endpoint-url=http://host.docker.internal:4567 s3 cp ./data.json s3://$(AWS_STORAGE_BUCKET_NAME)

dc-build-movie-server:
	docker-compose --profile movie_server build

dc-build-load-runner:
	docker-compose --profile load_runner build

dc-build: dc-build-movie-server

dc-start: dc-build awslocal-create-bucket awslocal-upload-data
	docker-compose --profile movie_server up

dc-stress: dc-build dc-build-load-runner
	docker-compose --profile load_runner up

local-start-infra:
	-docker-compose -f local-infra.yml -p movie-dev-infra up
