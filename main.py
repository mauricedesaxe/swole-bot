import sys
import os
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
)
from scrape import download_urls
from dotenv import load_dotenv

load_dotenv()

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "scrape":
            # Run the scraping function directly
            download_urls()
        elif sys.argv[1] == "query" and len(sys.argv) > 2:
            # Check if data directory exists and has files
            if not os.path.exists("data") or not os.listdir("data"):
                print("No data found. Please run 'make scrape' first to download the data.")
                sys.exit(1)
            
            # Check if storage already exists
            PERSIST_DIR = "./storage"
            if not os.path.exists(PERSIST_DIR):
                # Load the documents and create the index
                documents = SimpleDirectoryReader("data").load_data()
                index = VectorStoreIndex.from_documents(documents)
                # Store it for later
                index.storage_context.persist(persist_dir=PERSIST_DIR)
            else:
                # Load the existing index
                storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
                index = load_index_from_storage(storage_context)

            # Query the index
            query_engine = index.as_query_engine()
            response = query_engine.query(sys.argv[2])
            print("\nResponse: ", response)
        else:
            print("Invalid command. Use 'make help' to see available commands.")
            sys.exit(1)

if __name__ == "__main__":
    main()
