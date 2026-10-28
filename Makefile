.PHONY: help
help:
	@echo "Main:"
	@echo "  make help                 — Display this help"
	@echo "  make test                 — Run test suite"
	@echo "  make coverage             — Run test suite with text coverage"
	@echo "  make coverage-html        — Run test suite with html coverage"
	@echo "Local development:"
	@echo "  make local-build          — Build for local development"
	@echo "  make local-build-force    — Force build for local development"
	@echo "  make local-up             — Brings up for local development"
	@echo "  make local-django-exec    — Enter the local development django container"
	@echo "  make local-postgres-exec  — Enter the local development postgres container"
	@echo "Prod:"
	@echo "  make prod-build           — Build for prod"
	@echo "  make prod-build-force     — Force build for prod"
	@echo "  make prod-up              — Brings up for prod"
	@echo "  make prod-django-exec     — Enter the prod django container"
	@echo "  make prod-postgres-exec   — Enter the prod postgres container"	
	@echo "General development:"
	@echo "  make reset-db             — Reset postgres database of local development"

.PHONY: test
test:
	@docker exec -it declprofs-dev bash -c "python manage.py test"

.PHONY: coverage
coverage:
	@docker exec -it declprofs-dev bash -c "coverage run manage.py test"
	@docker exec -it declprofs-dev bash -c "coverage report"

.PHONY: coverage-html
coverage-html:
	@docker exec -it declprofs-dev bash -c "coverage run manage.py test"
	@docker exec -it declprofs-dev bash -c "coverage html"

.PHONY: local-build
local-build:
	@docker compose -f docker-compose-dev.yml build

.PHONY: local-build-force
local-build-force:
	@docker compose -f docker-compose-dev.yml build --force-rm --no-cache --pull

.PHONY: local-up
local-up:
	@docker compose -f docker-compose-dev.yml up

.PHONY: local-django-exec
local-django-exec:
	@docker exec -it --user root declprofs-dev bash

.PHONY: local-postgres-exec
local-postgres-exec:
	@docker exec -it --user root declprofs-postgres-dev bash

.PHONY: prod-build
prod-build:
	@docker compose -f docker-compose.yml build

.PHONY: prod-build-force
prod-build-force:
	@docker compose -f docker-compose.yml build --force-rm --no-cache --pull

.PHONY: prod-up
prod-up:
	@docker compose -f docker-compose.yml up

.PHONY: prod-django-exec
prod-django-exec:
	@docker exec -it --user root declprofs-prod bash

.PHONY: prod-postgres-exec
prod-postgres-exec:
	@docker exec -it --user root declprofs-postgres-prod bash

.PHONY: reset-db
reset-db:
	@docker compose down -v
