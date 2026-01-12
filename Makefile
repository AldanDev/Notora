#!make
.DEFAULT_GOAL := format

# Makefile target args
args = $(filter-out $@,$(MAKECMDGOALS))

# Command shortcuts
mypy = uv run mypy
pyright = uv run pyright
pytest = uv run pytest
ruff = uv run ruff

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

.PHONY: lint-python
lint-python: python-lint

.PHONY: python-lint
python-lint:
	$(ruff) check . --preview
	$(mypy)
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
