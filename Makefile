.PHONY: build push deploy test clean

IMAGE_NAME := ws_orchestration
ECR_REGISTRY := $(AWS_ACCOUNT_ID).dkr.ecr.us-east-1.amazonaws.com
IMAGE_TAG := latest

build:
	docker build -t $(IMAGE_NAME):$(IMAGE_TAG) .

tag:
	docker tag $(IMAGE_NAME):$(IMAGE_TAG) $(ECR_REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)

login:
	aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $(ECR_REGISTRY)

push: build tag login
	docker push $(ECR_REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)

test:
	docker run --rm \
		-e AWS_ACCESS_KEY_ID=$(AWS_ACCESS_KEY_ID) \
		-e AWS_SECRET_ACCESS_KEY=$(AWS_SECRET_ACCESS_KEY) \
		-e S3_BUCKET=$(S3_BUCKET) \
		$(IMAGE_NAME):$(IMAGE_TAG)

clean:
	docker rmi $(IMAGE_NAME):$(IMAGE_TAG) || true
	docker rmi $(ECR_REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG) || true


