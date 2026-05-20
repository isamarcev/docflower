PYTHON ?= python3
VENV   ?= .venv

.PHONY: help setup venv install install-hooks pre-commit-all run lint fmt typecheck test build-exe clean

help:
	@echo "Доступні команди:"
	@echo "  make setup        — повна первинна налаштування (venv + deps + pre-commit hooks)"
	@echo "  make venv         — створити .venv"
	@echo "  make install      — поставити залежності (dev)"
	@echo "  make install-hooks— встановити pre-commit гачки в .git/hooks"
	@echo "  make pre-commit-all— прогнати pre-commit по всіх файлах"
	@echo "  make run          — запустити додаток"
	@echo "  make lint         — ruff check"
	@echo "  make fmt          — ruff format"
	@echo "  make typecheck    — mypy"
	@echo "  make test         — pytest"
	@echo "  make build-exe    — зібрати .exe через PyInstaller (для Windows)"
	@echo "  make clean        — почистити кеші та збірки"

setup: venv install install-hooks
	@echo ""
	@echo "Готово. Спробуйте: make run"

venv:
	$(PYTHON) -m venv $(VENV)

install:
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r requirements-dev.txt

install-hooks:
	$(VENV)/bin/pre-commit install

pre-commit-all:
	$(VENV)/bin/pre-commit run --all-files

run:
	PYTHONPATH=src $(VENV)/bin/python -m docflow.main.app

lint:
	$(VENV)/bin/ruff check src tests

fmt:
	$(VENV)/bin/ruff format src tests

typecheck:
	$(VENV)/bin/mypy src

test:
	PYTHONPATH=src $(VENV)/bin/pytest

build-exe:
	$(VENV)/bin/pyinstaller --noconfirm --windowed --name DocFlow \
		--add-data "src/docflow/presentation/styles:docflow/presentation/styles" \
		src/docflow/main/app.py

clean:
	rm -rf build dist *.spec
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .ruff_cache
