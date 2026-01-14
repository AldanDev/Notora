#!make
.DEFAULT_GOAL := format

# Makefile target args
args = $(filter-out $@,$(MAKECMDGOALS))

# Command shortcuts
mypy = MYPYPATH=src \
	uv run --group lint mypy
pyright = uv run --group lint pyright
pytest = uv run --group tests pytest
ruff = uv run --group lint --group tests ruff

.PHONY: format
format:
	$(ruff) format .
	$(ruff) check --fix .

.PHONY: sync
sync:
	uv sync --frozen --all-groups

.PHONY: test
test:
	$(pytest)

.PHONY: lint
lint:
	$(ruff) check . --preview
	$(mypy) src tests
	$(pyright)

.PHONY: clean
clean:
	rm -rf `find . -name __pycache__`
	rm -f `find . -type f -name '*.py[co]' `
	rm -f `find . -type f -name '*~' `
	rm -f `find . -type f -name '.*~' `
	rm -rf dist *.egg-info
	rm -rf .cache
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf htmlcov
	rm -f .coverage
	rm -f .coverage.*
	rm -rf .venv
	rm -rf artefacts
	rm -rf .hypothesis
