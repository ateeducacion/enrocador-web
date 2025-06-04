# Simplified Makefile for Enriscador Web

THEMES_DIR := downloads

.PHONY: up down download package clean destroy check-plugin

# Start the local WordPress environment using wp-env
up:
	npx wp-env start

# Stop the environment
down:
	npx wp-env stop

# Interactive download of a site into $(THEMES_DIR)
download:
	@read -p "Site URL: " URL; \
	read -p "Folder name: " NAME; \
	mkdir -p $(THEMES_DIR)/$$NAME; \
	python -m enriscador_web.main download $$URL $(THEMES_DIR)/$$NAME --theme-name $$NAME

# Package all themes in $(THEMES_DIR) into zip files
package:
	@for d in $(THEMES_DIR)/*; do \
	[ -d "$$d" ] || continue; \
	python -m enriscador_web.main package "$$d" --output "$$d.zip"; \
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
