.PHONY: help install hooks-install hooks-uninstall build lint type-check format format-check test test-unit test-integration test-all check check-fast check-all ci db-check db-generate supabase-start supabase-stop supabase-status start start-studio start-all database-start database-stop studio-build studio-lint studio-type-check studio-test-unit studio-test-integration studio-check-all

help:
	@echo "xScanner Studio (Frontend + Supabase)"
	@echo "  make install            # npm install"
	@echo "  make build              # production build"
	@echo "  make lint               # eslint"
	@echo "  make hooks-install      # activate managed git hooks"
	@echo "  make hooks-uninstall    # deactivate managed git hooks"
	@echo "  make type-check         # typescript check"
	@echo "  make test-unit          # vitest unit tests"
	@echo "  make test-integration   # vitest integration tests"
	@echo "  make test-all           # unit + integration"
	@echo "  make check-all          # format/lint/type/build/unit"
	@echo "  make supabase-start     # supabase start"
	@echo "  make supabase-stop      # supabase stop"
	@echo "  make start-all          # supabase + vite dev"

install:
	npm install

hooks-install:
	npm run hooks:install

hooks-uninstall:
	npm run hooks:uninstall

build:
	npm run build

lint:
	npm run lint

type-check:
	npm run type-check

format:
	npm run format

format-check:
	npm run format:check

test: test-all

test-unit:
	npm run test:unit

test-integration:
	npm run test:integration

test-all:
	npm run test:all

check: check-all

check-fast:
	npm run check:fast

check-all:
	npm run check:all

ci:
	npm run format:check
	npm run lint
	npm run type-check
	npm run build
	npm run test:unit

db-check:
	npm run db:check

db-generate:
	npm run db:generate

supabase-start:
	supabase start

supabase-stop:
	supabase stop

supabase-status:
	@supabase status || true

database-start: supabase-start

database-stop: supabase-stop

start: start-all

start-studio:
	npm run dev

start-all:
	@echo "Starting Supabase (if needed) and Studio dev server..."
	@supabase status >/dev/null 2>&1 || supabase start
	npm run dev

studio-build: build

studio-lint: lint

studio-type-check: type-check

studio-test-unit: test-unit

studio-test-integration: test-integration

studio-check-all: check-all