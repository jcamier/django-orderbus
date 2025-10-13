# Order Fulfillment API POC — Django + DRF + Google Pub/Sub

## 1. Objective
Create a **proof of concept (POC)** Django application demonstrating an event-driven logistics workflow using:
- Django + Django REST Framework (DRF)
- PostgreSQL
- Google Pub/Sub (Publish/Subscribe)
- Webhook ingress and egress
- RequestCatcher for testing external callbacks
  https://kainos-systems.requestcatcher.com/

The system should:
1. Accept an **Order Created** webhook (ingress).
2. Persist order + items in PostgreSQL.
3. Publish an event to **Google Pub/Sub** (`order.created`).
4. A **subscriber** listens for that event and sends an **egress webhook** (POST) to RequestCatcher.

---

## 2. Architecture Overview

```plaintext
External System (Shopify-like)
      ↓  (POST /webhooks/orders/create/)
Django API (DRF)
  ├─ Save Order + Items → PostgreSQL
  └─ Publish message → Pub/Sub topic: order.created
           ↓
  Subscriber process (local)
           ↓
  Egress POST → RequestCatcher (simulated external callback)
```

---

## 3. Environment

### Dependencies
- django
- djangorestframework
- psycopg2-binary
- google-cloud-pubsub
- httpx
- python-dotenv

### Dev Dependencies
- uv (fast Python package installer)
- black (code formatter)
- ruff (linter/formatter)
- pytest
- pytest-django
- pytest-mock

### Environment Variables
```bash
# Django Settings
SECRET_KEY=django-insecure-dev-key-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DB_NAME=orderdb
DB_USER=postgres
DB_PASS=postgres
DB_HOST=localhost
DB_PORT=5432

# Google Pub/Sub Configuration
PUBSUB_EMULATOR_HOST=localhost:8085
PUBSUB_PROJECT_ID=demo-poc
PUBSUB_TOPIC_ORDER_CREATED=order.created
PUBSUB_SUBSCRIPTION_ORDER_CREATED=order.created.local

# Webhook Configuration
WEBHOOK_OUTGOING_URL=https://your-name.requestcatcher.com/
```

**Note:** Django will dynamically construct the database connection string from individual DB_* variables.

### Local Pub/Sub Emulator
Option A (Docker):
```
docker run -p 8085:8085 -e PUBSUB_PROJECT1=demo-poc gcr.io/google.com/cloudsdktool/cloud-sdk:emulators gcloud beta emulators pubsub start --host-port=0.0.0.0:8085
```
Option B (gcloud CLI):
```
gcloud beta emulators pubsub start --host-port=localhost:8085
```

---

## 4. Docker Setup

### docker-compose.yml
```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    container_name: orderbus-postgres
    environment:
      POSTGRES_DB: orderdb
      POSTGRES_USER: orderuser
      POSTGRES_PASSWORD: orderpass
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U orderuser -d orderdb"]
      interval: 10s
      timeout: 5s
      retries: 5

  pubsub-emulator:
    image: gcr.io/google.com/cloudsdktool/cloud-sdk:emulators
    container_name: orderbus-pubsub
    command: gcloud beta emulators pubsub start --host-port=0.0.0.0:8085
    environment:
      PUBSUB_PROJECT1: demo-poc
    ports:
      - "8085:8085"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8085"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

### Makefile
```makefile
.PHONY: help setup up down logs shell migrate createsuperuser test subscriber clean

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup:  ## Initial setup: start containers, install deps, migrate
	docker-compose up -d
	pip install -r requirements.txt
	sleep 5
	python manage.py migrate
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
	python manage.py shell

migrate:  ## Run database migrations
	python manage.py makemigrations
	python manage.py migrate

createsuperuser:  ## Create Django superuser
	python manage.py createsuperuser

runserver:  ## Start Django development server
	python manage.py runserver

subscriber:  ## Start Pub/Sub subscriber (blocking)
	python manage.py subscribe_order_created

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
```

**Note:** Docker Compose automatically reads variables from your `.env` file. The database connection string is dynamically constructed in Django settings from `DB_NAME`, `DB_USER`, `DB_PASS`, `DB_HOST`, and `DB_PORT`.

---

## 5. Code Quality Tools

### pyproject.toml
```toml
[project]
name = "django-orderbus"
version = "0.1.0"
description = "Order Fulfillment POC with Django and Google Pub/Sub"
requires-python = ">=3.11"
dependencies = [
    "django>=5.0",
    "djangorestframework>=3.14",
    "psycopg2-binary>=2.9",
    "google-cloud-pubsub>=2.18",
    "httpx>=0.25",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
dev = [
    "black>=24.0",
    "ruff>=0.1",
    "pytest>=7.4",
    "pytest-django>=4.7",
    "pytest-mock>=3.12",
]

[tool.black]
line-length = 100
target-version = ['py311']
exclude = '''
/(
    \.git
  | \.venv
  | venv
  | \.eggs
  | \.tox
  | __pycache__
  | migrations
)/
'''

[tool.ruff]
line-length = 100
target-version = "py311"
exclude = [
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "*/migrations/*",
]

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]
ignore = [
    "E501",  # line too long (handled by black)
]

[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "orderbus.settings"
python_files = ["test_*.py", "*_test.py"]
testpaths = ["tests"]
markers = [
    "integration: marks tests as integration tests (deselect with '-m \"not integration\"')",
]
```

### Updated Makefile
```makefile
.PHONY: help setup up down logs shell migrate createsuperuser test subscriber clean format lint

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup:  ## Initial setup: start containers, install deps, migrate
	docker-compose up -d
	uv pip install -e ".[dev]"
	sleep 5
	python manage.py migrate
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
	python manage.py shell

migrate:  ## Run database migrations
	python manage.py makemigrations
	python manage.py migrate

createsuperuser:  ## Create Django superuser
	python manage.py createsuperuser

runserver:  ## Start Django development server
	python manage.py runserver

subscriber:  ## Start Pub/Sub subscriber (blocking)
	python manage.py subscribe_order_created

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
```

---

## 6. Models

### Order
| Field | Type | Notes |
|--------|------|-------|
| external_ref | CharField | Unique order ID |
| customer_name | CharField |  |
| customer_email | EmailField |  |
| shipping_address | TextField |  |
| total | DecimalField | max_digits=10, decimal_places=2 |
| created_at | DateTimeField | auto_now_add=True |

### OrderItem
| Field | Type | Notes |
|--------|------|-------|
| order | FK → Order | related_name="items" |
| sku | CharField |  |
| name | CharField |  |
| quantity | PositiveIntegerField |  |
| unit_price | DecimalField |  |

---

## 7. API Contract

### Endpoint
`POST /webhooks/orders/create/`

### Request
```json
{
  "order_id": "SO-10045",
  "customer": {"name": "Jane Doe", "email": "jane@example.com"},
  "items": [
    {"sku": "ABC123", "name": "Solar Panel", "quantity": 2, "unit_price": 150.0},
    {"sku": "XYZ789", "name": "Mounting Kit", "quantity": 1, "unit_price": 50.0}
  ],
  "shipping_address": "123 Main St, Austin, TX 78701",
  "total": 350.0
}
```

### Response
`201 Created`
```json
{"ok": true, "order_id": "SO-10045"}
```

### Egress Webhook Payload
```json
{
  "event": "order.created",
  "order_id": "SO-10045",
  "customer_name": "Jane Doe",
  "total": "350.00",
  "sent_at": "ISO-8601 timestamp"
}
```

---

## 8. Pub/Sub Integration

### Topics & Subscriptions
- Topic: `order.created`
- Subscription: `order.created.local`

### Publisher Behavior
- After saving order, publish JSON message:
```json
{
  "event": "order.created",
  "order_id": "<id>",
  "customer_name": "<name>",
  "total": "<amount>",
  "created_at": "<ISO-8601>"
}
```
- Use `google.cloud.pubsub_v1.PublisherClient`.
- Wait max 1–2s for message ID; log success.

### Subscriber Behavior
- Use `google.cloud.pubsub_v1.SubscriberClient`.
- Long-running streaming pull (management command: `python manage.py subscribe_order_created`).
- On message received:
  1. Parse JSON.
  2. POST payload to `WEBHOOK_OUTGOING_URL` (RequestCatcher) using `httpx`.
  3. Log response and `ack()` on success.

---

## 9. Acceptance Criteria
1. Django API accepts valid webhook and saves order + items.
2. A Pub/Sub message is published to `order.created`.
3. Subscriber receives message and sends egress POST.
4. RequestCatcher inbox shows JSON with `event: "order.created"`.
5. Logs confirm publish + subscriber success.

---

## 10. Testing (pytest)

### Unit Tests
- **Publisher test:** mock `PublisherClient.publish` to confirm payload and topic.
- **Subscriber test:** mock `httpx.post`; simulate Pub/Sub message and confirm correct POST + ack.

### Integration
- Run with emulator:
  - Start subscriber.
  - POST sample order.
  - Confirm RequestCatcher logs POST within seconds.

---

## 11. Future Enhancements
- Add Celery for async retries.
- Add HMAC verification for ingress.
- Add dead-letter subscriptions.
- Add OpenTelemetry tracing.
