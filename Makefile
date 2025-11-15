.PHONY: help install dev server start stop restart clean test lint format migrate db-push db-generate db-reset workers-start workers-stop workers-restart logs

# Default target
help:
	@echo "Moral Duel API - Available Commands"
	@echo "===================================="
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install          Install dependencies"
	@echo "  make db-generate      Generate Prisma client"
	@echo "  make db-push          Push database schema"
	@echo "  make db-reset         Reset database"
	@echo ""
	@echo "Development:"
	@echo "  make dev              Run development server with auto-reload"
	@echo "  make server           Run production server"
	@echo "  make start            Start server in background"
	@echo "  make stop             Stop background server"
	@echo "  make restart          Restart server"
	@echo ""
	@echo "Background Workers:"
	@echo "  make workers-start    Start background workers (Celery)"
	@echo "  make workers-stop     Stop background workers"
	@echo "  make workers-restart  Restart background workers"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make test             Run all tests"
	@echo "  make test-cov         Run tests with coverage"
	@echo "  make lint             Run linting checks"
	@echo "  make format           Format code with black"
	@echo ""
	@echo "Utilities:"
	@echo "  make logs             Show server logs"
	@echo "  make clean            Clean cache and temporary files"
	@echo ""

# Installation and setup
install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt
	@echo "Generating Prisma client..."
	PATH="$(PWD)/.venv/bin:$$PATH" prisma generate
	@echo "✅ Installation complete!"

# Database commands
db-generate:
	@echo "Generating Prisma client..."
	PATH="$(PWD)/.venv/bin:$$PATH" prisma generate
	@echo "✅ Prisma client generated!"

db-push:
	@echo "Pushing database schema..."
	python -m prisma db push
	@echo "✅ Database schema updated!"

db-reset:
	@echo "⚠️  WARNING: This will delete all data!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		rm -f moralduel.db; \
		python -m prisma db push; \
		echo "✅ Database reset complete!"; \
	else \
		echo "❌ Cancelled"; \
	fi

migrate:
	@echo "Creating migration..."
	python -m prisma migrate dev

# Development server
dev:
	@echo "Starting development server..."
	python main.py

server:
	@echo "Starting production server..."
	uvicorn main:app --host 0.0.0.0 --port 8000

# Background server management
start:
	@echo "Starting server in background..."
	@if [ -f .server.pid ]; then \
		echo "❌ Server is already running (PID: $$(cat .server.pid))"; \
	else \
		nohup python main.py > logs/server.log 2>&1 & echo $$! > .server.pid; \
		echo "✅ Server started (PID: $$(cat .server.pid))"; \
		echo "   Logs: logs/server.log"; \
	fi

stop:
	@echo "Stopping server..."
	@if [ -f .server.pid ]; then \
		kill $$(cat .server.pid) 2>/dev/null || true; \
		rm -f .server.pid; \
		echo "✅ Server stopped"; \
	else \
		echo "❌ Server is not running"; \
	fi

restart: stop
	@sleep 2
	@make start

# Background workers (for AI case generation, reward distribution, etc.)
workers-start:
	@echo "Starting background workers..."
	@mkdir -p logs
	@if [ -f .workers.pid ]; then \
		echo "❌ Workers are already running (PID: $$(cat .workers.pid))"; \
	else \
		echo "⚠️  Celery workers not yet configured"; \
		echo "   This will be implemented in Phase 8: Background Jobs"; \
		echo "   For now, you can run scheduled tasks manually"; \
	fi
	# Uncomment when Celery is configured:
	# nohup celery -A app.workers worker --loglevel=info > logs/workers.log 2>&1 & echo $$! > .workers.pid
	# echo "✅ Workers started (PID: $$(cat .workers.pid))"

workers-stop:
	@echo "Stopping background workers..."
	@if [ -f .workers.pid ]; then \
		kill $$(cat .workers.pid) 2>/dev/null || true; \
		rm -f .workers.pid; \
		echo "✅ Workers stopped"; \
	else \
		echo "❌ Workers are not running"; \
	fi

workers-restart: workers-stop
	@sleep 2
	@make workers-start

# Testing
test:
	@echo "Running tests..."
	pytest

test-cov:
	@echo "Running tests with coverage..."
	pytest --cov=app --cov-report=html --cov-report=term
	@echo "📊 Coverage report: htmlcov/index.html"

# Code quality
lint:
	@echo "Running linting checks..."
	@echo "Checking with flake8..."
	-flake8 app/ --max-line-length=120 --exclude=__pycache__
	@echo "Checking with mypy..."
	-mypy app/ --ignore-missing-imports

format:
	@echo "Formatting code with black..."
	black app/ --line-length=120
	@echo "✅ Code formatted!"

# Utilities
logs:
	@if [ -f logs/server.log ]; then \
		tail -f logs/server.log; \
	else \
		echo "❌ No logs found. Server might not be running in background."; \
		echo "   Run 'make start' to start server in background mode."; \
	fi

clean:
	@echo "Cleaning cache and temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage 2>/dev/null || true
	@echo "✅ Cleaned!"

# Create necessary directories
init-dirs:
	@mkdir -p logs
	@echo "✅ Directories created!"
