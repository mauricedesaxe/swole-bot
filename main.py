import sys
import os
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
    Settings,
)
from llama_index.core.chat_engine import SimpleChatEngine
from llama_index.llms.openai import OpenAI
from scrape import download_urls
from dotenv import load_dotenv
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.vector_stores.chroma.base import ChromaVectorStore
import chromadb

load_dotenv()

# Configure chunking parameters
parser = SimpleNodeParser.from_defaults(
    chunk_size=512,
    chunk_overlap=50
)

# Initialize Chroma
chroma_client = chromadb.PersistentClient(path="./chroma_db")
try:
    chroma_collection = chroma_client.get_collection("my_collection")
except:
    chroma_collection = chroma_client.create_collection("my_collection")

# Create vector store
vector_store = ChromaVectorStore(
    chroma_collection=chroma_collection
)
storage_context = StorageContext.from_defaults(
    vector_store=vector_store
)

def create_index_in_batches(directory, batch_size=10):
    try:
        # Get only existing Markdown files with full path check
        all_files = []
        for file in os.listdir(directory):
            full_path = os.path.join(directory, file)
            if file.endswith('.md') and os.path.exists(full_path):
                all_files.append(full_path)
                
        if not all_files:
            raise ValueError(f"No Markdown files found in {directory}")
            
        index = None
        successful_batches = False
        all_documents = []
        
        total_batches = (len(all_files) + batch_size - 1) // batch_size
        print(f"Processing {len(all_files)} files in {total_batches} batches...")
        
        for i in range(0, len(all_files), batch_size):
            batch_files = all_files[i:i + batch_size]
            try:
                reader = SimpleDirectoryReader(
                    input_files=batch_files,
                    recursive=False,
                )
                documents = reader.load_data()
                all_documents.extend(documents)
                
                successful_batches = True
                print(f"Successfully processed batch {i//batch_size + 1}/{total_batches}")
                
            except Exception as e:
                print(f"Error processing batch {i//batch_size + 1}: {str(e)}")
                continue
        
        if not successful_batches:
            raise ValueError("No batches were successfully processed")
        
        print("Creating index from processed documents...")
        if all_documents:
            # Show progress during indexing
            total_docs = len(all_documents)
            print(f"Starting indexing of {total_docs} documents...")
            
            # Create index in smaller chunks to show progress
            chunk_size = 20
            for i in range(0, total_docs, chunk_size):
                chunk = all_documents[i:i + chunk_size]
                if index is None:
                    index = VectorStoreIndex.from_documents(
                        chunk,
                        storage_context=storage_context,
                        show_progress=True  # Enable progress bar
                    )
                else:
                    index.insert_nodes(chunk)
                print(f"Indexed documents {i + 1} to {min(i + chunk_size, total_docs)} of {total_docs}")
            
            print("Saving index to storage...")
            index.storage_context.persist(persist_dir="./storage")
            print("Index saved successfully!")
            
        return index
        
    except Exception as e:
        print(f"Error creating index: {str(e)}")
        return None

def main():
    # Configure the OpenAI model with specific system instructions
    system_prompt = """You are a direct and helpful AI assistant. Focus on providing clear, actionable information without adding disclaimers about consulting healthcare providers. Users are aware of when they need to seek professional help. Provide straightforward answers to questions while maintaining accuracy."""
    
    Settings.llm = OpenAI(
        model="gpt-4-turbo", 
        temperature=0.0,
        system_prompt=system_prompt
    )
    
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
            try:
                if not os.path.exists(PERSIST_DIR):
                    print("Creating new index. This may take a few minutes...")
                    index = create_index_in_batches("data", batch_size=10)
                    if index is None:
                        raise ValueError("Failed to create index")
                    print("Index creation completed!")
                else:
                    print("Loading existing index...")
                    storage_context = StorageContext.from_defaults(
                        persist_dir=PERSIST_DIR,
                        vector_store=vector_store
                    )
                    index = load_index_from_storage(storage_context)
                    print("Index loaded successfully!")
                
                # Create a chat engine with custom configuration
                chat_engine = index.as_chat_engine(
                    chat_mode="simple",
                    verbose=True,
                    system_prompt=system_prompt
                )
                
                print("\nChat session started. Type 'exit' to end the conversation.")
                
                while True:
                    user_input = input("\nYou: ").strip()
                    if user_input.lower() in ['exit', 'quit']:
                        print("Goodbye!")
                        break
                        
                    response = chat_engine.chat(user_input)
                    print("\nAssistant:", response.response)
                    
            except Exception as e:
                print(f"Error initializing chat: {str(e)}")
                sys.exit(1)
        else:
            print("Invalid command. Use 'make help' to see available commands.")
            sys.exit(1)

if __name__ == "__main__":
    main()
