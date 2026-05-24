.PHONY: format lint functional

format:
	uv run ruff format

lint:
	uv run ruff check
	uv run ruff format --diff
	uv run ty check

integration:
	@.scripts/integration-test.sh
