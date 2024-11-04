import os
import json
from datetime import datetime
import chromadb
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, load_index_from_storage, Settings
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.chroma.base import ChromaVectorStore
from llama_index.core.schema import Document
from dotenv import load_dotenv
import re

def setup():
    """
    Initializes the environment and loads configuration settings.

    This function loads environment variables from a .env file, reads the configuration
    from a JSON file, validates the required parameters, and initializes the Chroma
    database and the OpenAI language model.

    Returns:
        StorageContext: The storage context containing the vector store.
        dict: The configuration settings loaded from the JSON file.
    """
    load_dotenv()  # Load environment variables from .env file
    with open('config.json') as f:
        config = json.load(f)  # Load configuration from JSON file
    
    # Validate config
    required_params = ["chunk_size", "chunk_overlap", "batch_size", "system_prompt", "model", "temperature"]
    if not all(config.get(param) for param in required_params):
        raise ValueError(f"Missing configuration parameters")  # Raise error if any required parameter is missing
    
    # Initialize Chroma and LLM
    client = chromadb.PersistentClient(path="./chroma_db")  # Create a persistent Chroma client
    collection = client.get_or_create_collection("my_collection")  # Get or create a collection in Chroma
    vector_store = ChromaVectorStore(chroma_collection=collection)  # Initialize the vector store with the Chroma collection
    Settings.llm = OpenAI(model=config['model'], temperature=config['temperature'], system_prompt=config['system_prompt'])  # Set the LLM settings
    
    return StorageContext.from_defaults(vector_store=vector_store), config  # Return the storage context and config

def process_documents(directory, batch_size):
    """
    Processes documents from a specified directory in batches.

    This function reads documents from the given directory, cleans the text by removing
    unwanted characters, and adds metadata such as character count and processing date.

    Args:
        directory (str): The path to the directory containing documents.
        batch_size (int): The number of documents to process in a batch.

    Returns:
        list: A list of cleaned Document objects with added metadata.
    """
    reader = SimpleDirectoryReader(input_dir=directory, recursive=False)  # Initialize the document reader
    documents = reader.load_data()  # Load documents from the directory
    
    # Clean and add metadata in batches
    cleaned_docs = []
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]  # Get the current batch of documents
        cleaned_docs.extend([
            Document(
                text=' '.join(re.sub(r'[^\w\s.,!?-]', '', doc.text).split()),  # Clean the text
                metadata={**doc.metadata, 'char_count': len(doc.text), 'processed_date': datetime.now().isoformat()}  # Add metadata
            ) for doc in batch
        ])
    
    return cleaned_docs  # Return the list of cleaned documents

def chat_session(storage_context, config):
    """
    Starts a chat session with the user.

    This function checks for existing data, creates or loads an index of documents,
    and facilitates a chat session where the user can interact with the assistant.

    Args:
        storage_context (StorageContext): The storage context for the vector store.
        config (dict): The configuration settings for the chat session.
    """
    if not os.path.exists("data") or not os.listdir("data"):
        print("No data found. Please run 'make scrape' first.")  # Prompt user to scrape data if none exists
        return

    PERSIST_DIR = "./storage"  # Directory to persist the index
    if not os.path.exists(PERSIST_DIR):
        print("Creating new index...")  # Inform user that a new index is being created
        documents = process_documents("data", config['batch_size'])  # Process documents from the data directory
        index = VectorStoreIndex.from_documents(documents, storage_context=storage_context, show_progress=True)  # Create a new index
        index.storage_context.persist(persist_dir=PERSIST_DIR)  # Persist the index to the storage directory
    else:
        print("Loading existing index...")  # Inform user that an existing index is being loaded
        index = load_index_from_storage(StorageContext.from_defaults(
            persist_dir=PERSIST_DIR, 
            vector_store=storage_context.vector_store
        ))  # Load the existing index

    chat_engine = index.as_chat_engine(chat_mode="simple", verbose=True, system_prompt=config['system_prompt'])  # Initialize the chat engine
    print("\nChat session started. Type 'exit' to end.")  # Inform user that the chat session has started

    while True:
        user_input = input("\nYou: ").strip()  # Get user input
        if user_input.lower() in ['exit', 'quit']:
            break  # Exit the chat session if the user types 'exit' or 'quit'
        print("\nAssistant:", chat_engine.chat(user_input).response)  # Get and print the assistant's response

if __name__ == "__main__":
    storage_context, config = setup()
    chat_session(storage_context, config)