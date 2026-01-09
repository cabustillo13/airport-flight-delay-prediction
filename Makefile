.ONESHELL:
ENV_PREFIX=$(shell python -c "if __import__('pathlib').Path('.venv/bin/pip').exists(): print('.venv/bin/')")

.PHONY: help
help:             	## Show the help.
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@fgrep "##" Makefile | fgrep -v fgrep

.PHONY: venv
venv:			## Create a virtual environment
	@echo "Creating virtualenv ..."
	@rm -rf .venv
	@python3 -m venv .venv
	@./.venv/bin/pip install -U pip
	@echo
	@echo "Run 'source .venv/bin/activate' to enable the environment"

.PHONY: install
install:		## Install dependencies
	pip install -r requirements-dev.txt
	pip install -r requirements-test.txt
	pip install -r requirements.txt

# IMPORTANT: Update this URL after deploying to GCP
# Run: make deploy-gcp
# Then update with the URL shown in the output
# Note: Also you can make local tests against the local Docker container (localhost:8080)
STRESS_URL = https://flight-delay-prediction-pg6oadgp5a-uc.a.run.app/

.PHONY: stress-test
stress-test:		## Run stress test against deployed API
	@echo "Running stress test against: $(STRESS_URL)"
	mkdir reports || true
	locust -f tests/stress/api_stress.py --print-stats --html reports/stress-test.html --run-time 60s --headless --users 100 --spawn-rate 1 -H $(STRESS_URL)

.PHONY: model-test
model-test:			## Run tests and coverage
	mkdir reports || true
	pytest --cov-config=.coveragerc --cov-report term --cov-report html:reports/html --cov-report xml:reports/coverage.xml --junitxml=reports/junit.xml --cov=challenge tests/model

.PHONY: api-test
api-test:			## Run tests and coverage
	mkdir reports || true
	pytest --cov-config=.coveragerc --cov-report term --cov-report html:reports/html --cov-report xml:reports/coverage.xml --junitxml=reports/junit.xml --cov=challenge tests/api

.PHONY: build
build:			## Build locally the python artifact
	python setup.py bdist_wheel

.PHONY: docker-build
docker-build:		## Build Docker image locally
	docker build -t flight-delay-api:latest .

.PHONY: docker-run
docker-run:		## Run Docker container locally
	docker run -d -p 8080:8080 --name flight-delay flight-delay-api:latest
	@echo "API running at http://localhost:8080"
	@echo "Health: http://localhost:8080/health"
	@echo "Docs: http://localhost:8080/docs"

.PHONY: docker-stop
docker-stop:		## Stop and remove Docker container
	docker stop flight-delay || true
	docker rm flight-delay || true

.PHONY: deploy-gcp
deploy-gcp:		## Deploy to Google Cloud Run
	@chmod +x deploy-gcp.sh
	@./deploy-gcp.sh

.PHONY: gcp-logs
gcp-logs:		## View Cloud Run logs
	gcloud run services logs read flight-delay-prediction --region=us-central1 --limit=50

.PHONY: gcp-delete
gcp-delete:		## Delete Cloud Run service
	gcloud run services delete flight-delay-prediction --region=us-central1 --quiet