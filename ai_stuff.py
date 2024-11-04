import os
import json
import concurrent.futures
from datetime import datetime
from typing import List
from tqdm import tqdm
import chromadb
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
    Settings,
)
from llama_index.llms.openai import OpenAI
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.vector_stores.chroma.base import ChromaVectorStore
from llama_index.core.schema import Document
from dotenv import load_dotenv

def load_config():
    load_dotenv()
    with open('config.json') as config_file:
        config = json.load(config_file)
    return config

def check_required_params(config):
    required_params = {
        "chunk_size": config['chunk_size'],
        "chunk_overlap": config['chunk_overlap'],
        "batch_size": config['batch_size'],
        "system_prompt": config['system_prompt'],
        "model": config['model'],
        "temperature": config['temperature']
    }
    for param, value in required_params.items():
        if value is None:
            raise ValueError(f"Missing configuration parameter: {param}")

def initialize_chroma():
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
    return ChromaVectorStore(chroma_collection=chroma_collection)

def create_index_in_batches(directory, storage_context, batch_size):
    def process_batch(batch_files):
        try:
            reader = SimpleDirectoryReader(input_files=batch_files, recursive=False)
            documents = reader.load_data()
            return preprocess_documents(documents)
        except Exception as e:
            print(f"Error processing batch: {str(e)}")
            return []

    try:
        all_files = [
            os.path.join(directory, f) for f in os.listdir(directory)
            if f.endswith('.md') and os.path.exists(os.path.join(directory, f))
        ]
        
        if not all_files:
            raise ValueError(f"No Markdown files found in {directory}")
        
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
        
        if all_documents:
            index = VectorStoreIndex.from_documents(
                documents=all_documents,
                storage_context=storage_context,
                show_progress=True,
                use_async=True
            )
            index.storage_context.persist(persist_dir="./storage")
            return index
            
    except Exception as e:
        print(f"Error creating index: {str(e)}")
        return None

def preprocess_documents(documents):
    def clean_text(text: str) -> str:
        import re
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s.,!?-]', '', text)
        return text.strip()
    
    processed_docs: List[Document] = []
    for doc in documents:
        cleaned_text = clean_text(doc.text)
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

def setup_ai():
    config = load_config()
    check_required_params(config)
    parser = SimpleNodeParser.from_defaults(
        chunk_size=config['chunk_size'],
        chunk_overlap=config['chunk_overlap']
    )
    vector_store = initialize_chroma()
    storage_context = StorageContext.from_defaults(
        vector_store=vector_store
    )
    return storage_context, config

def initialize_llm(config):
    Settings.llm = OpenAI(
        model=config['model'], 
        temperature=config['temperature'],
        system_prompt=config['system_prompt']
    )

def chat_session(storage_context, config):
    # Check if data directory exists and has files
    if not os.path.exists("data") or not os.listdir("data"):
        print("No data found. Please run 'make scrape' first to download the data.")
        return
    
    # Check if storage already exists
    PERSIST_DIR = "./storage"
    try:
        if not os.path.exists(PERSIST_DIR):
            print("Creating new index. This may take a few minutes...")
            index = create_index_in_batches("data", storage_context, config['batch_size'])
            if index is None:
                raise ValueError("Failed to create index")
            print("Index creation completed!")
        else:
            print("Loading existing index...")
            storage_context = StorageContext.from_defaults(
                persist_dir=PERSIST_DIR,
                vector_store=initialize_chroma()
            )
            index = load_index_from_storage(storage_context)
            print("Index loaded successfully!")
        
        # Create a chat engine with custom configuration
        chat_engine = index.as_chat_engine(
            chat_mode="simple",
            verbose=True,
            system_prompt=config['system_prompt']
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