.PHONY: help install dev-install test lint format clean run run-enhanced docs

# Default target
help:
	@echo "Multi-Agent Database Chatbot - Available Commands:"
	@echo ""
	@echo "  install      - Install package and dependencies"
	@echo "  dev-install  - Install with development dependencies"
	@echo "  test         - Run tests"
	@echo "  lint         - Run linting (flake8, mypy)"
	@echo "  format       - Format code (black)"
	@echo "  clean        - Clean temporary files"
	@echo "  run          - Run basic API server"
	@echo "  run-enhanced - Run enhanced API server"
	@echo "  docs         - Generate documentation"
	@echo "  health       - Check system health"

# Installation
install:
	pip install -e .

dev-install:
	pip install -e ".[dev,test]"

# Testing
test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=app --cov=clients --cov-report=html --cov-report=term

# Code quality
lint:
	flake8 app/ clients/ tests/
	mypy app/ clients/

format:
	black app/ clients/ tests/
	isort app/ clients/ tests/

# Cleanup
clean:
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name "*.pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/

# Running the application
run:
	python -m app.main

# Development mode
run-dev:
	uvicorn app.main:app --host 0.0.0.0 --port 9000 --reload

# Documentation
docs:
	@echo "Documentation available at:"
	@echo "  - API Docs: http://localhost:9000/docs (when running)"

# Health checks
health:
	curl -s http://localhost:9000/health | python -m json.tool || echo "Server not running"

health-enhanced:
	curl -s http://localhost:9000/health | python -m json.tool || echo "Server not running"

# Database helpers
test-gold-db:
	@echo " Testing Gold Database Connection..."
	python3 scripts/test_gold_db_connection.py

setup-gold-db:
	@echo " Setting up Gold Database Configuration..."
	python3 scripts/setup_gold_db.py

chatbot:
	@echo " Starting Gold Database Chatbot (CLI)..."
	python3 scripts/gold_chatbot.py

chatbot-web:
	@echo " Starting Gold Database Chatbot (Web)..."
	@echo "Open browser at: http://localhost:8080"
	python3 scripts/gold_chatbot_web.py

# Development helpers
setup-env:
	cp config/.env.example.extended .env
	@echo "Environment file created. Please edit .env with your credentials."

check-deps:
	pip check

update-deps:
	pip install --upgrade -r deployments/requirements.txt

# Docker commands
docker-build:
	docker build -t multi-agent-chatbot .

docker-run:
	docker run -p 8000:8000 --env-file .env multi-agent-chatbot

# Database helpers
check-db:
	@echo "Checking database connectivity..."
	python -c "from app.database import sql_executor; import asyncio; asyncio.run(sql_executor.get_schema_info())"

# LLM client checks
check-llm:
	@echo "Checking LLM client connectivity..."
	python -c "from app.llm_manager_extended import extended_llm_manager; import asyncio; print(asyncio.run(extended_llm_manager.health_check()))"

# Full system check
system-check: check-deps check-db check-llm
	@echo "System check completed!"

# Development workflow
dev: format lint test
	@echo "Development workflow completed!"

# Production deployment prep
prep-prod:
	@echo "Preparing for production deployment..."
	@echo "1. Ensure .env is configured"
	@echo "2. Run 'make test' to verify functionality"
	@echo "3. Run 'make clean' to remove temporary files"
	@echo "4. Build Docker image with 'make docker-build'"
