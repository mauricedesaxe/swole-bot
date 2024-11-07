import os
from datetime import datetime
import chromadb
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, load_index_from_storage, Settings
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.chroma.base import ChromaVectorStore
from llama_index.core.schema import Document
from dotenv import load_dotenv
import re
from llama_index.core.node_parser import HierarchicalNodeParser
from config import CONFIG

def setup():
    """
    Initializes the environment and loads configuration settings.

    This function loads environment variables from a .env file, reads the configuration
    from a JSON file, validates the required parameters, and initializes the Chroma
    database and the OpenAI language model.

    Returns:
        StorageContext: The storage context containing the vector store.
    """
    load_dotenv()  # Load environment variables from .env file
    
    # Initialize Chroma and LLM
    client = chromadb.PersistentClient(path="./chroma_db")  # Create a persistent Chroma client
    collection = client.get_or_create_collection("my_collection")  # Get or create a collection in Chroma
    vector_store = ChromaVectorStore(chroma_collection=collection)  # Initialize the vector store with the Chroma collection
    Settings.llm = OpenAI(model=CONFIG['model'], temperature=CONFIG['temperature'], system_prompt=CONFIG['system_prompt'])  # Set the LLM settings
    
    return StorageContext.from_defaults(vector_store=vector_store)  # Return the storage context and config

def process_documents(directory, batch_size):
    """
    Processes documents using multi-level semantic chunking.
    """
    reader = SimpleDirectoryReader(input_dir=directory, recursive=False)
    documents = reader.load_data()
    
    # Create hierarchical chunking configuration
    chunk_sizes = {
        "text": CONFIG['chunk_size'],          # Base text chunks
        "sentence": 100,                       # Sentence-level chunks
        "paragraph": CONFIG['chunk_size'] * 2  # Paragraph-level chunks
    }
    
    # Initialize hierarchical parser with multi-level chunking
    node_parser = HierarchicalNodeParser.from_defaults(
        chunk_sizes=[chunk_sizes["sentence"], chunk_sizes["text"], chunk_sizes["paragraph"]],
        include_metadata=True
    )
    
    cleaned_docs = []
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        
        for doc in batch:
            # Preserve more semantic markers in text cleaning
            cleaned_text = re.sub(r'[^\w\s.,!?;:()\n\-\[\]"]', '', doc.text)
            
            # Parse document into hierarchical nodes
            nodes = node_parser.get_nodes_from_documents(
                [Document(text=cleaned_text, metadata={"source": doc.metadata.get("file_path", "")})]
            )
            
            # Convert nodes while preserving hierarchical relationships
            for node_idx, node in enumerate(nodes):
                metadata = {
                    **doc.metadata,
                    **node.metadata,
                    'char_count': len(node.text),
                    'processed_date': datetime.now().isoformat(),
                    'chunk_index': node_idx,
                    'total_chunks': len(nodes),
                    'original_doc_id': doc.doc_id,
                    'level': node.metadata.get('level', 0),
                    'section': node.metadata.get('section_name', None)
                }
                
                cleaned_docs.append(Document(text=node.text, metadata=metadata))
    
    return cleaned_docs

def chat_session(storage_context):
    """
    Starts a chat session with the user.

    This function checks for existing data, creates or loads an index of documents,
    and facilitates a chat session where the user can interact with the assistant.

    Args:
        storage_context (StorageContext): The storage context for the vector store.
        config (dict): The configuration settings for the chat session.
    """
    if not os.path.exists("data") or not os.listdir("data"):
        print("No data found. Please run 'make scrape' first.")
        return
    
    # Get the Chroma collection from the vector store
    chroma_collection = storage_context.vector_store._collection
    
    # Check if collection has any documents
    collection_count = chroma_collection.count()
    
    if collection_count == 0:
        print("Creating new index...")
        documents = process_documents("data", CONFIG['batch_size'])
        index = VectorStoreIndex.from_documents(
            documents, 
            storage_context=storage_context, 
            show_progress=True
        )
    else:
        print("Loading existing index...")
        try:
            index = VectorStoreIndex.from_vector_store(
                storage_context.vector_store
            )
        except Exception as e:
            print(f"Error loading existing index: {str(e)}")
            print("Creating new index instead...")
            documents = process_documents("data", CONFIG['batch_size'])
            index = VectorStoreIndex.from_documents(
                documents, 
                storage_context=storage_context, 
                show_progress=True
            )

    chat_engine = index.as_chat_engine(
        chat_mode="context",
        verbose=True,
        system_prompt=CONFIG['system_prompt'],
        node_relationships=True,
        similarity_top_k=5,  # Retrieve more related chunks
        context_window=4096  # Allow for larger context window
    )
    print("\nChat session started. Type 'exit' to end.")

    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ['exit', 'quit']:
            break
        print("\nAssistant:", chat_engine.chat(user_input).response)

if __name__ == "__main__":
    storage_context, config = setup()
    chat_session(storage_context)