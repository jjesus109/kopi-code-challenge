
.PHONY: help install test run down clean logs shell

# Default target - show help
help: ## Show this help message
	@echo "Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "For more information about a command, run: make <command>"

# Installation commands
install: ## Install all requirements to run the service
	@echo "Installing requirements..."
	@if ! command -v python3 &> /dev/null; then \
		echo "Python 3 is required but not installed."; \
		echo "Please install Python 3.8+ from https://www.python.org/downloads/"; \
		exit 1; \
	fi
	@if ! command -v pip3 &> /dev/null; then \
		echo "pip3 is required but not installed."; \
		echo "Please install pip3 or upgrade Python to include pip."; \
		exit 1; \
	fi
	@if ! command -v docker &> /dev/null; then \
		echo "Docker is required but not installed."; \
		echo "Please install Docker from https://docs.docker.com/get-docker/"; \
		exit 1; \
	fi
	@if ! command -v docker-compose &> /dev/null; then \
		echo "Docker Compose is required but not installed."; \
		echo "Please install Docker Compose from https://docs.docker.com/compose/install/"; \
		exit 1; \
	fi
	@echo "All required tools are installed."
	@echo "Installing Python dependencies..."
	@if [ -f "pyproject.toml" ]; then \
		echo "Using pyproject.toml for dependencies..."; \
		if ! command -v uv &> /dev/null; then \
			echo "uv is not installed. Installing uv..."; \
			pip3 install uv; \
		fi; \
		python3 -m uv sync; \
	else \
		echo "No requirements.txt or pyproject.toml found. Skipping Python dependency installation."; \
	fi
	@echo "Installation completed successfully!"

# Testing commands
test: ## Run tests
	@echo "Running tests..."
	@if [ -f "pytest.ini" ] || [ -f "pyproject.toml" ]; then \
		source .venv/bin/activate; \
		pytest tests/ -v; \
	else \
		echo "No pytest configuration found. Please ensure pytest.ini or pyproject.toml exists."; \
		exit 1; \
	fi



# Docker commands
run: ## Run the service and all related services in Docker
	@echo "Starting services with Docker Compose..."
	@if [ -f "docker-compose.yml" ]; then \
		docker-compose up -d; \
		echo "Services started. Check logs with: make logs"; \
	else \
		echo "docker-compose.yml not found. Please ensure it exists."; \
		exit 1; \
	fi

restart: ## Restart the service and all related services in Docker
	@echo "Restarting services with Docker Compose..."
	@if [ -f "docker-compose.yml" ]; then \
		docker-compose restart; \
		echo "Services restarted."; \
		docker-compose logs -f; \
	else \
		echo "docker-compose.yml not found. Please ensure it exists."; \
		exit 1; \
	fi


logs: ## Show logs from running services
	@echo "Showing service logs..."
	@if [ -f "docker-compose.yml" ]; then \
		docker-compose logs -f; \
	else \
		echo "docker-compose.yml not found."; \
		exit 1; \
	fi

down: ## Teardown of all running services
	@echo "Stopping all services..."
	@if [ -f "docker-compose.yml" ]; then \
		docker-compose down; \
		echo "All services stopped."; \
	else \
		echo "docker-compose.yml not found."; \
		exit 1; \
	fi

clean: ## Teardown and removal of all containers
	@echo "Cleaning up all containers and volumes..."
	@if [ -f "docker-compose.yml" ]; then \
		docker-compose down -v --remove-orphans; \
		docker system prune -f; \
		echo "Cleanup completed."; \
	else \
		echo "docker-compose.yml not found."; \
		exit 1; \
	fi


shell: ## Open a shell in the main service container
	@echo "Opening shell in main service container..."
	@if [ -f "docker-compose.yml" ]; then \
		docker-compose exec app /bin/bash; \
	else \
		echo "docker-compose.yml not found."; \
	fi

# Default target
.DEFAULT_GOAL := help
