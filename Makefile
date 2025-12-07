.PHONY: help install migrate runserver test clean docker-build docker-up docker-down

help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make migrate      - Run database migrations"
	@echo "  make runserver    - Start development server"
	@echo "  make test         - Run tests"
	@echo "  make clean        - Clean Python cache files"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-up    - Start Docker containers"
	@echo "  make docker-down  - Stop Docker containers"

install:
	pip install -r requirements.txt

migrate:
	python manage.py migrate

runserver:
	python manage.py runserver

test:
	python manage.py test

clean:
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete

docker-build:
	docker-compose build

docker-up:
	docker-compose up

docker-down:
	docker-compose down

