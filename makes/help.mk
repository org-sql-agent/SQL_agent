.PHONY: help
help:
	@echo "Available commands:"
	@grep -Eh '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) | \
	sed -E 's|^([a-zA-Z0-9_-]+):.*## |\1## |' | \
	sort | awk 'BEGIN {FS = "## "}; {printf "  \033[36m%-24s\033[0m %s\n", $$1, $$2}'