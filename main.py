import sys
import os
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
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
                
            documents = SimpleDirectoryReader("data").load_data()
            index = VectorStoreIndex.from_documents(documents)
            query_engine = index.as_query_engine()
            response = query_engine.query(sys.argv[2])
            print("\nResponse: ", response)
        else:
            print("Invalid command. Use 'make help' to see available commands.")
            sys.exit(1)

if __name__ == "__main__":
    main()
