# We're using Make as a command runner.
MAKEFLAGS += --always-make

format:
	uv run ruff check --fix
	uv run ruff format

lint:
	uv run ruff check
	uv run ruff format --diff
	uv run ty check

integration:
	.scripts/integration-test.sh
