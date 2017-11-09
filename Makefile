SHELL = /bin/bash
APP_ENV ?= dev

deploy: build
	aws cloudformation deploy \
		--stack-name river-gauges-app-$(APP_ENV) \
		--template-file tmp/sam-template-output.yaml \
		--capabilities CAPABILITY_IAM

build: build/lambda build/sam

build/lambda: clean
	mkdir -p tmp/lambda_code && \
	pip install requests -t tmp/lambda_code && \
	cp gauges.py tmp/lambda_code && \
	cd tmp/lambda_code && \
	zip -r9 ../lambda_deployment_package.zip .

build/sam:
	aws cloudformation package \
		--template-file sam-template.yaml \
		--s3-bucket aws-on-tap \
		--s3-prefix river-gauges-app \
		--output-template-file tmp/sam-template-output.yaml

clean:
	rm -rf tmp/*
