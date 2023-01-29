conf:
ENV?=dev
include .env.$(ENV)
export

local-start-server: conf
	cd src/py_movie_db && uvicorn app.main:app --reload --port 8100 --no-use-colors

awslocal-create-bucket: conf
	-awslocal --endpoint-url=http://host.docker.internal:4567 s3api create-bucket --bucket $(AWS_STORAGE_BUCKET_NAME) --create-bucket-configuration "{\"LocationConstraint\": \"$(AWS_DEFAULT_REGION)\"}"

awslocal-upload-data: conf
	awslocal --endpoint-url=http://host.docker.internal:4567 s3 cp ./data.json s3://$(AWS_STORAGE_BUCKET_NAME)

dc-build-movie-server: conf
	docker-compose --profile movie_server build

dc-build-load-runner: conf
	docker-compose --profile load_runner build

dc-start-infra: conf
	-docker-compose -f local-infra.yml -p movie-dev-infra up

dc-start: conf dc-build-movie-server awslocal-create-bucket awslocal-upload-data
	docker-compose --profile movie_server up

dc-stress: conf dc-build-load-runner
	docker-compose --profile load_runner up
