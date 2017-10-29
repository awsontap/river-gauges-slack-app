SHELL = /bin/bash

deploy: build
	aws cloudformation deploy \
		--template-file tmp/sam-template-output.yaml \
		--stack-name river-guages-app

build:
	aws cloudformation package \
		--template-file sam-template.yaml \
		--s3-bucket aws-on-tap \
		--s3-prefix river-guages-app \
		--output-template-file tmp/sam-template-output.yaml
