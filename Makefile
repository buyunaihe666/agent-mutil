.PHONY: dev build up down test test-backend test-frontend lint lint-backend lint-frontend clean help

help:
	@echo "NEXUS AI Development Commands"
	@echo "============================="
	@echo "make dev           - Start development servers"
	@echo "make build         - Build all Docker images"
	@echo "make up            - Start all services via Docker Compose"
	@echo "make down          - Stop all services"
	@echo "make test          - Run all tests"
	@echo "make test-backend  - Run backend tests"
	@echo "make test-frontend - Run frontend tests"
	@echo "make lint          - Run all linters"
	@echo "make lint-backend  - Run Ruff on backend"
	@echo "make lint-frontend - Run Biome on frontend"
	@echo "make clean         - Remove generated files"

dev:
	cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
	cd frontend && npm run dev

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

test: test-backend test-frontend

test-backend:
	cd backend && uv run pytest -v

test-frontend:
	cd frontend && npm run test

lint: lint-backend lint-frontend

lint-backend:
	cd backend && uv run ruff check .

lint-frontend:
	cd frontend && npx biome check .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
