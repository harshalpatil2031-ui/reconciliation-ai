SHELL := /bin/sh
DB_SERVICE := db
DB_NAME ?= reconciliation
DB_USER ?= reconciliation
S ?= 1

.PHONY: up down schema counts snapshot restore test openapi

up:
	docker compose up --build -d --wait

down:
	docker compose down

schema:
	@for file in sql/01_extensions_and_schema.sql sql/02_frustum_and_spatial.sql sql/03_audit_hash_chain.sql; do \
		if [ -f "$$file" ]; then \
			docker compose exec -T $(DB_SERVICE) psql -v ON_ERROR_STOP=1 -U $(DB_USER) -d $(DB_NAME) -f "/docker-entrypoint-initdb.d/$$(basename "$$file")"; \
		fi; \
	done

counts:
	docker compose exec -T $(DB_SERVICE) psql -U $(DB_USER) -d $(DB_NAME) -c "SELECT 'events' AS table_name, count(*) FROM events UNION ALL SELECT 'parcels', count(*) FROM parcels UNION ALL SELECT 'cases', count(*) FROM cases UNION ALL SELECT 'official_assessments', count(*) FROM official_assessments UNION ALL SELECT 'scene_observations', count(*) FROM scene_observations UNION ALL SELECT 'observed_estimates', count(*) FROM observed_estimates UNION ALL SELECT 'hazard_context', count(*) FROM hazard_context UNION ALL SELECT 'detections', count(*) FROM detections UNION ALL SELECT 'photos', count(*) FROM photos UNION ALL SELECT 'audit_log', count(*) FROM audit_log UNION ALL SELECT 'reviews', count(*) FROM reviews ORDER BY 1;"

snapshot:
	@mkdir -p handoffs/stage$(S)
	docker compose exec -T $(DB_SERVICE) pg_dump -U $(DB_USER) -d $(DB_NAME) -Fc > handoffs/stage$(S)/stage$(S).dump

restore:
	test -f handoffs/stage$(S)/stage$(S).dump
	docker compose exec -T $(DB_SERVICE) pg_restore --clean --if-exists --no-owner -U $(DB_USER) -d $(DB_NAME) < handoffs/stage$(S)/stage$(S).dump

test:
	python -m pytest

openapi:
	python scripts/export_openapi.py
