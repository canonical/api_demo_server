# We're using Make as a command runner.
MAKEFLAGS += --always-make

format:
	uv run ruff format
	uv run ruff check --fix

lint:
	uv run ruff check
	uv run ruff format --diff
	uv run ty check

integration:
	.scripts/register-rock.sh
	.scripts/test-compose.sh
