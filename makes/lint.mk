.PHONY: lint
lint: ## 使用 flake8 檢查程式碼風格（app/ + tests/）
	poetry run flake8 .

.PHONY: format
format: ## 使用 isort + black 自動格式化程式碼（app/ + tests/）
	poetry run isort .
	poetry run black .