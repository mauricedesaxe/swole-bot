.PHONY: scrape chat

# Default target
all: help

help:
	@echo "Available commands:"
	@echo "  make scrape    - Run the scraper to download data"
	@echo "  make query q='Your question'    - Query the data with your question"
	@echo "  make stats    - Get index statistics"
	@echo "  make cleanup    - Cleanup old embeddings"

# Run the scraper
scrape:
	poetry run python main.py scrape

# Chat with the data
chat:
	poetry run python main.py chat

clean-data:
	rm -rf ./data/*

clean-storage:
	rm -rf ./storage/*

clean-chroma:
	rm -rf ./chroma_db/*