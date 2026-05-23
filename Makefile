.PHONY: format, lint

format:
	uv run ruff format

lint:
	uv run ruff check
	uv run ruff format --diff
	uv run ty check
