# Idea Inc - Makefile
# Common commands for development and deployment

.PHONY: help install dev test lint format docker-up docker-down docker-build clean

# Default target
help:
	@echo "Idea Inc - Available Commands"
	@echo ""
	@echo "Development:"
	@echo "  make install      - Install Python dependencies"
	@echo "  make dev          - Start all services for development"
	@echo "  make dev-auth     - Start auth service only"
	@echo "  make dev-sim      - Start simulation service only"
	@echo "  make dev-ai       - Start AI service only"
	@echo ""
	@echo "Testing:"
	@echo "  make test         - Run all tests"
	@echo "  make test-auth    - Run auth service tests"
	@echo "  make test-sim     - Run simulation service tests"
	@echo "  make lint         - Run linter"
	@echo "  make format       - Format code"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up    - Start all services with Docker"
	@echo "  make docker-down  - Stop all Docker services"
	@echo "  make docker-build - Build Docker images"
	@echo "  make docker-logs  - View Docker logs"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean        - Clean up generated files"
	@echo "  make db-migrate   - Run database migrations"

# =============================================================================
# Development
# =============================================================================

install:
	pip install -r requirements.txt

dev:
	@echo "Starting all services..."
	docker-compose up -d postgres mongodb redis
	@echo "Waiting for databases..."
	sleep 5
	@echo "Starting application services..."
	$(MAKE) dev-auth &
	$(MAKE) dev-sim &
	$(MAKE) dev-ai &

dev-auth:
	cd services/auth_service && uvicorn main:app --reload --port 8000

dev-sim:
	cd services/simulation_service && uvicorn main:app --reload --port 8001

dev-ai:
	cd services/ai_service && uvicorn main:app --reload --port 8002

# =============================================================================
# Testing
# =============================================================================

test:
	pytest tests/ -v --cov=services --cov-report=term-missing

test-auth:
	pytest tests/auth/ -v

test-sim:
	pytest tests/simulation/ -v

test-ai:
	pytest tests/ai/ -v

# =============================================================================
# Code Quality
# =============================================================================

lint:
	ruff check services/ shared/ tests/

format:
	ruff format services/ shared/ tests/

type-check:
	mypy services/ shared/

# =============================================================================
# Docker
# =============================================================================

docker-up:
	docker-compose up -d

docker-up-full:
	docker-compose --profile observability up -d

docker-up-kafka:
	docker-compose --profile kafka up -d

docker-down:
	docker-compose down

docker-down-volumes:
	docker-compose down -v

docker-build:
	docker-compose build

docker-logs:
	docker-compose logs -f

docker-logs-auth:
	docker-compose logs -f auth-service

docker-logs-sim:
	docker-compose logs -f simulation-service

docker-logs-ai:
	docker-compose logs -f ai-service

docker-ps:
	docker-compose ps

# =============================================================================
# Database
# =============================================================================

db-migrate:
	cd services/auth_service && alembic upgrade head

db-rollback:
	cd services/auth_service && alembic downgrade -1

db-reset:
	docker-compose down -v
	docker-compose up -d postgres mongodb redis
	sleep 5
	$(MAKE) db-migrate

# =============================================================================
# Utilities
# =============================================================================

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	find . -type d -name ".ruff_cache" -delete
	find . -type d -name ".mypy_cache" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/

# Generate proto files (if using gRPC)
proto:
	python -m grpc_tools.protoc \
		-I shared/proto \
		--python_out=shared/proto \
		--grpc_python_out=shared/proto \
		shared/proto/*.proto

# Create a new service scaffold
new-service:
	@read -p "Service name: " name; \
	mkdir -p services/$$name-service/app/api; \
	touch services/$$name-service/__init__.py; \
	touch services/$$name-service/app/__init__.py; \
	touch services/$$name-service/app/api/__init__.py; \
	echo "Created services/$$name-service/"

# Show environment info
info:
	@echo "Python: $$(python --version)"
	@echo "Pip: $$(pip --version)"
	@echo "Docker: $$(docker --version)"
	@echo "Docker Compose: $$(docker-compose --version)"

