conf:
ENV?=dev
include .env.$(ENV)
export

local-start-server: conf
	cd src/py_movie_db && uvicorn app.main:app --reload --port 8100 --no-use-colors

awslocal-create-bucket: conf
	-awslocal --endpoint-url=$(AWS_ENDPOINT_URL_LOCAL) s3api create-bucket --bucket $(AWS_STORAGE_BUCKET_NAME) --create-bucket-configuration "{\"LocationConstraint\": \"$(AWS_DEFAULT_REGION)\"}"

awslocal-upload-data: conf
	awslocal --endpoint-url=$(AWS_ENDPOINT_URL_LOCAL) s3 cp ./data.json s3://$(AWS_STORAGE_BUCKET_NAME)

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

build: conf
	docker build -t $(DOCKER_REGISTRY)/movie_db_server:latest src/py_movie_db
	docker push $(DOCKER_REGISTRY)/movie_db_server:latest

k8s-delete:
	-kubectl delete ingress movie-server-ingress
	-kubectl delete service movie-server
	-kubectl delete deploy movie-server
	-kubectl delete secret aws-secret
	-kubectl delete configmap movies-env

k8s-create:
	kubectl create -f ./infra/configmap.yaml
	kubectl create -f ./infra/secrets.yaml
	kubectl create -f ./infra/deployment.yaml
	kubectl create -f ./infra/service.yaml
	kubectl create -f ./infra/ingress.yaml

k8s-replace:
	kubectl replace -f ./infra/configmap.yaml
	kubectl replace -f ./infra/secrets.yaml
	kubectl replace -f ./infra/deployment.yaml
	kubectl replace -f ./infra/service.yaml
	kubectl replace -f ./infra/ingress.yaml
