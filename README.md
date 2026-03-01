# xScanner Studio

Frontend repository for xScanner Studio (React + TypeScript + Vite) with local Supabase.

## Quick Start

```bash
npm install
cp .env.example .env.local
make start-all
```

Studio runs on `http://localhost:8084`.

## Main Commands

```bash
make build
make lint
make test-unit
make test-integration
make check-all
make supabase-start
make supabase-stop
```

## Repository Scope

- This repository contains only the Studio frontend and Supabase resources.
- Python backend code lives in the original backend repository and is not part of this repo lifecycle.

## Documentation

- Architecture and design docs: `docs/studio/`
