.PHONY: help build setup up down logs shell migrate createsuperuser test subscriber clean format lint

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build:  ## Install dependencies with uv
	uv pip install -e ".[dev]"

setup:  ## Initial setup: start containers, install deps, migrate
	docker-compose up -d
	make build
	sleep 5
	.venv/bin/python manage.py migrate
	@echo "✓ Setup complete. Run 'make createsuperuser' to create admin user."

up:  ## Start all containers
	docker-compose up -d

down:  ## Stop all containers
	docker-compose down

logs:  ## Tail logs from all containers
	docker-compose logs -f

db-logs:  ## Tail logs from database only
	docker-compose logs -f db

pubsub-logs:  ## Tail logs from Pub/Sub emulator
	docker-compose logs -f pubsub-emulator

shell:  ## Django shell
	.venv/bin/python manage.py shell

migrate:  ## Run database migrations
	.venv/bin/python manage.py makemigrations
	.venv/bin/python manage.py migrate

createsuperuser:  ## Create Django superuser
	.venv/bin/python manage.py createsuperuser

runserver:  ## Start Django development server
	.venv/bin/python manage.py runserver

subscriber:  ## Start Pub/Sub subscriber (blocking)
	.venv/bin/python manage.py subscribe_order_created

format:  ## Format code with black
	black .

lint:  ## Lint code with ruff
	ruff check .

lint-fix:  ## Lint and auto-fix with ruff
	ruff check --fix .

check:  ## Run both format and lint checks
	black --check .
	ruff check .

test:  ## Run pytest tests
	pytest -v

test-integration:  ## Run integration tests (requires emulator)
	PUBSUB_EMULATOR_HOST=localhost:8085 pytest -v -m integration

clean:  ## Stop containers and remove volumes
	docker-compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

reset:  ## Full reset: clean, setup, and migrate
	make clean
	make setup

