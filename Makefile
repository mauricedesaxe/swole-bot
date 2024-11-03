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

# Chat with the data
chat:
	python main.py chat