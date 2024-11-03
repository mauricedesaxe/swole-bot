import sys
import os
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
    Settings,
)
from llama_index.core.chat_engine import CondenseQuestionChatEngine
from llama_index.llms.openai import OpenAI
from scrape import download_urls
from dotenv import load_dotenv

load_dotenv()

def main():
    # Configure the OpenAI model
    Settings.llm = OpenAI(model="gpt-4-turbo", temperature=0.0)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "scrape":
            download_urls()
        elif sys.argv[1] == "chat":
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

            # Create a chat engine
            chat_engine = index.as_chat_engine(
                chat_mode="condense_question",
                verbose=True
            )

            print("\nChat session started. Type 'exit' to end the conversation.")
            
            while True:
                user_input = input("\nYou: ").strip()
                if user_input.lower() in ['exit', 'quit']:
                    print("Goodbye!")
                    break
                    
                response = chat_engine.chat(user_input)
                print("\nAssistant:", response.response)
        else:
            print("Invalid command. Use 'make help' to see available commands.")
            sys.exit(1)

if __name__ == "__main__":
    main()
