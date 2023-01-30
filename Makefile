conf:
ENV?=dev
include .env.$(ENV)
export

awslocal-create-buckets: conf
	-awslocal --endpoint-url=$(AWS_ENDPOINT_URL_LOCAL) s3api create-bucket --bucket $(AWS_INBOX_BUCKET_NAME) --create-bucket-configuration "{\"LocationConstraint\": \"$(AWS_DEFAULT_REGION)\"}"
	-awslocal --endpoint-url=$(AWS_ENDPOINT_URL_LOCAL) s3api create-bucket --bucket $(AWS_STORAGE_BUCKET_NAME) --create-bucket-configuration "{\"LocationConstraint\": \"$(AWS_DEFAULT_REGION)\"}"
	-awslocal --endpoint-url=$(AWS_ENDPOINT_URL_LOCAL) s3api create-bucket --bucket $(AWS_ARCHIVE_BUCKET_NAME) --create-bucket-configuration "{\"LocationConstraint\": \"$(AWS_DEFAULT_REGION)\"}"

awslocal-seed-inbox: conf
	awslocal --endpoint-url=$(AWS_ENDPOINT_URL_LOCAL) s3 cp ./src/movie_indexer_job/data/seed_data.json s3://$(AWS_INBOX_BUCKET_NAME)/db.json

awslocal-seed-main-db: conf
	awslocal --endpoint-url=$(AWS_ENDPOINT_URL_LOCAL) s3 cp ./src/movie_indexer_job/data/seed_data.json s3://$(AWS_STORAGE_BUCKET_NAME)/increment1.json

test:
	cd src/movie_indexer_job && poetry run python -m pytest -o log_cli=true
	cd src/py_movie_db && poetry run python -m pytest -o log_cli=true

local-seed:
	cd src/movie_indexer_job && poetry run python seed.py

local-start-server: conf
	cd src/py_movie_db && uvicorn app.main:app --reload --port 8100 --no-use-colors

dc-build-movie-server: conf
	docker-compose --profile movie_server build

dc-build-load-runner: conf
	docker-compose --profile load_runner build

dc-build-movie-indexer: conf
	docker-compose --profile movie_indexer build

dc-start-infra: conf
	-docker-compose -f local-infra.yml -p movie-dev-infra up

dc-seed: conf dc-build-movie-indexer
	docker-compose --profile movie_seed up

dc-start: conf test dc-build-movie-server awslocal-create-bucket awslocal-upload-data
	docker-compose --profile movie_server up

dc-stress: conf dc-build-load-runner
	docker-compose --profile load_runner up

dc-ingest: conf dc-build-movie-indexer
	docker-compose --profile movie_indexer up

build: conf test
	docker build -t $(DOCKER_REGISTRY)/movie_db_server:latest src/py_movie_db
	docker push $(DOCKER_REGISTRY)/movie_db_server:latest
	docker build -t $(DOCKER_REGISTRY)/movie_indexer:latest src/movie_indexer_job
	docker push $(DOCKER_REGISTRY)/movie_indexer:latest

k8s-seed-delete:
	-kubectl delete job seed-db

k8s-seed: k8s-seed-delete
	kubectl create -f ./infra/seed-job.yaml

k8s-create: k8s-seed
	kubectl create -f ./infra/configmap.yaml
	kubectl create -f ./infra/secrets.yaml
	kubectl create -f ./infra/deployment.yaml
	kubectl create -f ./infra/service.yaml
	kubectl create -f ./infra/ingress.yaml
	kubectl create -f ./infra/ingest-cronjob.yaml

k8s-replace:
	kubectl replace -f ./infra/ingest-cronjob.yaml
	kubectl replace -f ./infra/configmap.yaml
	kubectl replace -f ./infra/secrets.yaml
	kubectl replace -f ./infra/deployment.yaml
	kubectl replace -f ./infra/service.yaml
	kubectl replace -f ./infra/ingress.yaml

k8s-delete:
	-kubectl delete ingress movie-server-ingress
	-kubectl delete service movie-server
	-kubectl delete deploy movie-server
	-kubectl delete job seed-db
	-kubectl delete cronjob ingest-cronjob
	-kubectl delete secret aws-secret
	-kubectl delete configmap movies-env

k8s-stress-clean:
	-helm uninstall locust
	-kubectl delete configmap movie-locustfile

k8s-stress:
	-helm uninstall locust
	-kubectl delete configmap movie-locustfile
	kubectl create configmap movie-locustfile --from-file ./src/load_runner/main.py
	helm upgrade --install locust deliveryhero/locust -f ./infra/config/locus-values.yaml
