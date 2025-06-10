						# Simplified Makefile for enrocador Web

# Default target shows the list of available commands
.DEFAULT_GOAL := help

THEMES_DIR := downloads

.PHONY: help up down activate download package clean destroy check-plugin install
VENV_DIR ?= env

# Show available targets
help:
	@echo "Available targets:"
	@echo "  help            Show this help message"
	@echo "  up              Start the local WordPress environment using wp-env"
	@echo "  down            Stop the environment"
	@echo "  check-venv      Check if virtualenv is active (prints red/green warning)"
	@echo "  download        Interactive download of a site into $(THEMES_DIR)"
	@echo "  package         Create zip archives from each theme in $(THEMES_DIR)"
	@echo "  clean           Remove wp-env environments"
	@echo "  destroy         Remove all wp-env containers and volumes"
	@echo "  check-plugin    Run plugin-check in the environment"
	@echo "  install         Install Python and set up virtualenv"

# Start the local WordPress environment using wp-env
up:
	npx wp-env start
	# Enable all themes in $(THEMES_DIR) on the network using WP-CLI inside the wp-env container
	@for d in $(THEMES_DIR)/*; do \
	  [ -d "$$d" ] || continue; \
	  slug=$$(basename $$d); \
	  printf "Enabling theme '$$slug' on the network...\n"; \
	  npx wp-env run cli wp theme enable $$slug --network || exit 1; \
	done
	@printf "\033[0;32mAll themes in '$(THEMES_DIR)' have been network-enabled.\033[0m\n"



# Stop the environment
down:
	npx wp-env stop

# Comprueba si estamos dentro del virtualenv; imprime en rojo si no y en verde si sí.
check-venv:
	@ if [ -z "$$VIRTUAL_ENV" ]; then \
	    printf "\033[0;31m[ERROR] Virtualenv no detectado. Actívalo con:\n    source $(VENV_DIR)/bin/activate\033[0m\n"; \
	    exit 1; \
	  else \
	    printf "\033[0;32m[OK] Virtualenv activo en: $$VIRTUAL_ENV\033[0m\n"; \
	  fi

# Interactive download of a site into $(THEMES_DIR)
download: check-venv
	@read -p "Site URL: " URL; \
	read -p "Folder name: " NAME; \
	mkdir -p $(THEMES_DIR)/$$NAME; \
	python -m enrocador_web.main download $$URL $(THEMES_DIR)/$$NAME --theme-name $$NAME

# Package all themes in $(THEMES_DIR) into zip files
package: check-venv
	@for d in $(THEMES_DIR)/*; do \
	[ -d "$$d" ] || continue; \
	python -m enrocador_web.main package "$$d" --output "$$d.zip"; \
	done

# Clean the environments, the same as running "npx wp-env clean all"
clean:
	npx wp-env clean development
	npx wp-env clean tests

# Remove all wp-env containers and volumes
destroy:
	npx wp-env destroy

# Pass the wp plugin-check
check-plugin: up
	npx wp-env run cli wp plugin install plugin-check --activate --color
	npx wp-env run cli wp plugin check decker --exclude-directories=tests --exclude-checks=file_type,image_functions --ignore-warnings --color

# Install Python (Windows) and create a virtual environment
install:
	@if [ "$(OS)" = "Windows_NT" ]; then \
	if ! command -v py >/dev/null 2>&1; then \
	winget install -e --id Python.Python.3.12; \
	fi; \
	py -3.12 -m venv $(VENV_DIR) || py -3 -m venv $(VENV_DIR); \
	$(VENV_DIR)\\Scripts\\pip install -r requirements.txt; \
	else \
	python3 -m venv $(VENV_DIR); \
	$(VENV_DIR)/bin/pip install -r requirements.txt; \
	fi
