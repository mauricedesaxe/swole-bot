.PHONY: scrape query

# Default target
all: help

# Help message
help:
	@echo "Available commands:"
	@echo "  make scrape    - Run the scraper to download data"
	@echo "  make query q='Your question'    - Query the data with your question"

# Run the scraper
scrape:
	python main.py scrape

# Query the data
query:
	@if [ -z "$(q)" ]; then \
		echo "Please provide a question using q='Your question'"; \
		exit 1; \
	fi
	python main.py query "$(q)"