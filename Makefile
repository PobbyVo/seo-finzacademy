.PHONY: dev migrate api web test-api lint-api lint-web typecheck check build-web test-e2e

dev:
	npm run dev

migrate:
	cd services/api && .venv/bin/python -m alembic upgrade head

api: migrate
	cd services/api && .venv/bin/python -m uvicorn finz_api.main:app --host 127.0.0.1 --port 8000 --reload

web:
	cd apps/web && npm run dev

test-api:
	cd services/api && .venv/bin/python -m pytest -q

lint-api:
	cd services/api && .venv/bin/python -m ruff check .

lint-web:
	cd apps/web && npm run lint

typecheck:
	cd apps/web && npm run typecheck

check: test-api lint-api lint-web typecheck

build-web:
	cd apps/web && npm run build

test-e2e:
	cd e2e && npm test
