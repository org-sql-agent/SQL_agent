.PHONY: export-requirements
export-requirements: ## Export dependencies to requirements.txt
	poetry export -f requirements.txt --output requirements.txt --without-hashes

.PHONY: add remove

add: ## 加入套件並更新 requirements.txt
	@if [ "$(words $(MAKECMDGOALS))" -le 1 ]; then \
		echo "Usage: make add <package1> [package2 ...]"; \
		exit 1; \
	fi
	poetry add $(filter-out $@,$(MAKECMDGOALS))
	poetry export -f requirements.txt --output requirements.txt --without-hashes

remove: ## 移除套件並更新 requirements.txt
	@if [ "$(words $(MAKECMDGOALS))" -le 1 ]; then \
		echo "Usage: make remove <package1> [package2 ...]"; \
		exit 1; \
	fi
	poetry remove $(filter-out $@,$(MAKECMDGOALS))
	poetry export -f requirements.txt --output requirements.txt --without-hashes

# 防止 make 嘗試執行 add/numpy 等目標
%:
	@: