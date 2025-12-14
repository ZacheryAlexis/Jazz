# Makefile for Jazz project - useful dev helpers
.PHONY: smoke start stop build-frontend

smoke:
	./scripts/smoke_test.sh

start:
	./start_all.sh

stop:
	./stop_all.sh

build-frontend:
	npm --prefix frontend run build
