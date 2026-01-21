#!make
.DEFAULT_GOAL := format

# Makefile target args
args = $(filter-out $@,$(MAKECMDGOALS))

# Command shortcuts
mypy = MYPYPATH=src \
	uv run --group lint mypy
pyright = uv run --group lint pyright
stubtest = MYPYPATH=src PYTHONPATH=src \
	uv run --group lint stubtest
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
postgres_version:=latest
test:
	$(pytest) --postgres-version $(postgres_version)

.PHONY: lint
lint:
	$(ruff) check . --preview
	$(mypy) src tests
	$(pyright)
	$(MAKE) stubtest

.PHONY: stubtest
stubtest:
	@modules=$$(find src/notora -name '*.pyi' -print \
		| sed -e 's#^src/##' -e 's#/#.#g' -e 's#\.pyi$$##' -e 's#\.__init__$$##'); \
	if [ -z "$$modules" ]; then \
		echo "No .pyi modules found under src/notora"; \
		exit 1; \
	fi; \
	$(stubtest) $$modules

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
	rm -rf .hypothesis
