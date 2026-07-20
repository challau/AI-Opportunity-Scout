.PHONY: help up down dev build logs ps clean migrate seed crawl test frontend backend

# ── Help ───────────────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  🚀 AI Opportunity Scout — Available Commands"
	@echo ""
	@echo "  Docker:"
	@echo "    make up         Start all services (Docker Compose)"
	@echo "    make down       Stop all services"
	@echo "    make logs       Show service logs"
	@echo "    make ps         Show running containers"
	@echo "    make build      Build Docker images"
	@echo "    make clean      Remove volumes and images"
	@echo ""
	@echo "  Database:"
	@echo "    make migrate    Run Alembic migrations"
	@echo "    make seed       Load sample data"
	@echo ""
	@echo "  Development:"
	@echo "    make backend    Start backend (uvicorn, hot reload)"
	@echo "    make frontend   Start frontend (Next.js dev)"
	@echo "    make dev        Start both backend + frontend locally"
	@echo ""
	@echo "  Tools:"
	@echo "    make crawl      Trigger immediate crawl of all platforms"
	@echo "    make test       Run backend tests"
	@echo ""

# ── Docker ─────────────────────────────────────────────────────────────────────
up:
	docker compose up -d
	@echo "✅ All services started. Frontend: http://localhost:3000 | API: http://localhost:8000"

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

ps:
	docker compose ps

clean:
	docker compose down -v --rmi local

# ── Database ───────────────────────────────────────────────────────────────────
migrate:
	cd backend && alembic upgrade head

seed:
	docker compose exec postgres psql -U postgres -d ai_opportunity_scout -f /docker-entrypoint-initdb.d/seed.sql

# ── Development ────────────────────────────────────────────────────────────────
setup: ## Initial project setup
	@cp -n .env.example .env 2>/dev/null || true
	@echo "✅ .env created from .env.example — fill in your API keys!"
	@echo "   Then run: make up"

backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	cd frontend && npm run dev

dev:
	@echo "Starting backend and frontend in parallel..."
	$(MAKE) -j2 backend frontend

install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

# ── Tools ──────────────────────────────────────────────────────────────────────
crawl:
	curl -s -X POST http://localhost:8000/api/ai/trigger-crawl?platform=all \
		-H "Authorization: Bearer $$(cat .token 2>/dev/null || echo '')" | python3 -m json.tool

test:
	cd backend && pytest -v --tb=short

format:
	cd backend && black app/ && isort app/
	cd frontend && npm run lint --fix
