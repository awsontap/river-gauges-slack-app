SHELL = /bin/bash

deploy: build
	aws cloudformation deploy \
		--stack-name river-guages-app \
		--template-file tmp/sam-template-output.yaml \
		--capabilities CAPABILITY_IAM

build: build/lambda build/sam

build/lambda: clean
	mkdir -p tmp/lambda_code && \
	pip install requests -t tmp/lambda_code && \
	cp guages.py tmp/lambda_code && \
	cd tmp/lambda_code && \
	zip -r9 ../lambda_deployment_package.zip .

build/sam:
	aws cloudformation package \
		--template-file sam-template.yaml \
		--s3-bucket aws-on-tap \
		--s3-prefix river-guages-app \
		--output-template-file tmp/sam-template-output.yaml

clean:
	rm tmp/lambda_deployment_package.zip && \
	rm -rf tmp/lambda_code
