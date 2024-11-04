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
from datetime import datetime
from typing import List
from llama_index.core.schema import Document
import concurrent.futures
from tqdm import tqdm

load_dotenv()

# Configure chunking parameters
parser = SimpleNodeParser.from_defaults(
    chunk_size=512,
    chunk_overlap=50
)

# Initialize Chroma
chroma_client = chromadb.PersistentClient(
    path="./chroma_db",
    settings=chromadb.Settings(
        anonymized_telemetry=False,
        allow_reset=True,
        is_persistent=True
    )
)
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

def create_index_in_batches(directory, batch_size=20):
    def process_batch(batch_files):
        try:
            reader = SimpleDirectoryReader(input_files=batch_files, recursive=False)
            documents = reader.load_data()
            return preprocess_documents(documents)
        except Exception as e:
            print(f"Error processing batch: {str(e)}")
            return []

    try:
        # Get all markdown files
        all_files = [
            os.path.join(directory, f) for f in os.listdir(directory)
            if f.endswith('.md') and os.path.exists(os.path.join(directory, f))
        ]
        
        if not all_files:
            raise ValueError(f"No Markdown files found in {directory}")
        
        # Process files in parallel batches
        total_batches = (len(all_files) + batch_size - 1) // batch_size
        all_documents = []
        
        with tqdm(total=len(all_files), desc="Processing documents") as pbar:
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                futures = []
                for i in range(0, len(all_files), batch_size):
                    batch_files = all_files[i:i + batch_size]
                    futures.append(executor.submit(process_batch, batch_files))
                
                for future in concurrent.futures.as_completed(futures):
                    batch_documents = future.result()
                    all_documents.extend(batch_documents)
                    pbar.update(len(batch_documents))
        
        # Create index with optimized settings
        if all_documents:
            index = VectorStoreIndex.from_documents(
                documents=all_documents,
                storage_context=storage_context,
                show_progress=True,
                use_async=True  # Enable async processing
            )
            
            # Save index
            index.storage_context.persist(persist_dir="./storage")
            return index
            
    except Exception as e:
        print(f"Error creating index: {str(e)}")
        return None

def preprocess_documents(documents):
    def clean_text(text: str) -> str:
        import re
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s.,!?-]', '', text)
        return text.strip()
    
    processed_docs: List[Document] = []
    for doc in documents:
        # Clean the text content
        cleaned_text = clean_text(doc.text)
        # Create new document with cleaned text
        processed_doc = Document(
            text=cleaned_text,
            metadata={
                **doc.metadata,
                'char_count': len(cleaned_text),
                'processed_date': datetime.now().isoformat()
            }
        )
        processed_docs.append(processed_doc)
    
    return processed_docs

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

def get_index_stats():
    try:
        collection = chroma_client.get_collection("my_collection")
        count = collection.count()
        return {
            "total_documents": count,
            "collection_name": collection.name,
            "metadata": collection.metadata
        }
    except Exception as e:
        return {"error": str(e)}

def cleanup_old_embeddings(days_old=30):
    from datetime import datetime, timedelta
    cutoff_date = datetime.now() - timedelta(days=days_old)
    
    try:
        collection = chroma_client.get_collection("my_collection")
        # Get all documents with their metadata
        docs = collection.get()
        
        # Find IDs of old documents
        old_ids = [
            id for id, metadata in zip(docs['ids'], docs['metadatas'])
            if metadata.get('processed_date') and 
            datetime.fromisoformat(metadata['processed_date']) < cutoff_date
        ]
        
        if old_ids:
            collection.delete(ids=old_ids)
            print(f"Removed {len(old_ids)} old documents from the index")
    except Exception as e:
        print(f"Error cleaning up old embeddings: {str(e)}")

if __name__ == "__main__":
    main()
