# Simplified Makefile for Enriscador Web

THEMES_DIR := themes
DOWNLOADS_DIR := downloads

.PHONY: up down download package

# Start the local WordPress environment using wp-env
up:
	npx wp-env start

# Stop the environment
down:
	npx wp-env stop

# Interactive download of a site into $(DOWNLOADS_DIR)
download:
	@read -p "Site URL: " URL; \
	read -p "Folder name: " NAME; \
	mkdir -p $(DOWNLOADS_DIR)/$$NAME; \
	python -m enriscador_web.main download $$URL $(DOWNLOADS_DIR)/$$NAME --theme-name $$NAME

# Package all downloads in $(DOWNLOADS_DIR) into themes under $(THEMES_DIR)
package:
	@for d in $(DOWNLOADS_DIR)/*; do \
		[ -d "$$d" ] || continue; \
		python -m enriscador_web.main package "$$d" --output "$$d.zip"; \
	done
