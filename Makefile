.PHONY: up down migrate seed dev demo logs reset test

up:
	docker compose up --build -d postgres redis minio

down:
	docker compose down

migrate:
	docker compose run --rm api python -m app.db_bootstrap

seed:
	docker compose run --rm api python -m db.seed.seed_data

dev:
	docker compose up --build -d api worker frontend

logs:
	docker compose logs -f api worker frontend

reset:
	docker compose down -v
	$(MAKE) up
	sleep 5
	$(MAKE) migrate
	$(MAKE) seed

demo: reset dev
	@echo "Waiting for services to come up..."
	sleep 8
	open http://localhost:3000 || xdg-open http://localhost:3000 || true

test:
	docker compose run --rm api pytest -q
