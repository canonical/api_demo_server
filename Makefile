# We're using Make as a command runner.
MAKEFLAGS += --always-make

format:
	uv run ruff format
	uv run ruff check --fix

lint:
	uv run --locked ruff check
	uv run --locked ruff format --diff
	uv run --locked ty check

integration:
	.scripts/integration-test.sh
