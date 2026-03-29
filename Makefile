.PHONY: setup generate test test-cov lint clean help

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup: ## First-time setup: install deps + generate parser
	uv sync --all-extras
	$(MAKE) generate

generate: ## Regenerate ANTLR parser from grammar files
	uv run python scripts/generate_parser.py

test: ## Run tests
	uv run pytest -v

test-cov: ## Run tests with coverage report
	uv run pytest -v --cov=pylintool --cov-report=term-missing

lint: ## Run pylintool on its own source
	uv run pylintool src/

clean: ## Remove generated files and caches
	rm -f src/pylintool/generated/PyWhitespace*.py
	rm -f src/pylintool/generated/*.interp src/pylintool/generated/*.tokens
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .coverage
