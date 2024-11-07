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
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.node_parser import TokenTextSplitter
from config import CONFIG
import concurrent.futures
from tqdm import tqdm
import multiprocessing
from transformers import pipeline

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

def clean_text(text):
    # Remove special characters while preserving meaningful punctuation
    cleaned = re.sub(r'[^\w\s.,!?;:()\n\-\[\]"\'$%]', ' ', text)
    # Normalize whitespace
    cleaned = ' '.join(cleaned.split())
    # Remove repeated punctuation
    cleaned = re.sub(r'([.,!?])\1+', r'\1', cleaned)
    return cleaned

def extract_metadata(text):
    metadata = {
        'processed_date': datetime.now().isoformat(),
        'word_count': len(text.split()),
        'char_count': len(text),
        'sentences': len(re.split(r'[.!?]+', text)),
        'has_numbers': bool(re.search(r'\d', text)),
        'has_citations': bool(re.search(r'\[\d+\]|\(\d{4}\)', text))
    }
    return metadata

def process_document_batch(batch, node_parser):
    """Process a single batch of documents"""
    batch_docs = []
    for doc in batch:
        # Enhanced text cleaning
        cleaned_text = clean_text(doc.text)
        
        # Extract rich metadata
        base_metadata = extract_metadata(cleaned_text)
        base_metadata.update({"source": doc.metadata.get("file_path", "")})
        
        # Create document with enhanced metadata
        batch_docs.append(Document(text=cleaned_text, metadata=base_metadata))
    
    # Process with enhanced node parser
    nodes = node_parser.get_nodes_from_documents(batch_docs)
    
    cleaned_docs = []
    for doc, node in zip(batch_docs, nodes):
        # Detect semantic sections for each chunk
        section_info = detect_semantic_sections(node.text)
        
        # Combine all metadata
        metadata = {
            **doc.metadata,
            **node.metadata,
            **section_info,
            'chunk_index': len(cleaned_docs),
            'total_chunks': len(nodes),
            'level': node.metadata.get('level', 0),
            'next_chunk_id': node.relationships.get('next', None),
            'prev_chunk_id': node.relationships.get('previous', None)
        }
        
        cleaned_docs.append(Document(text=node.text, metadata=metadata))
    
    return cleaned_docs

def process_documents(directory, batch_size):
    reader = SimpleDirectoryReader(input_dir=directory, recursive=False)
    documents = reader.load_data()
    
    # Create enhanced node parser
    node_parser = create_enhanced_node_parser()
    
    # Use larger batch size since we have plenty of RAM
    batch_size = min(50, len(documents))
    batches = [documents[i:i + batch_size] for i in range(0, len(documents), batch_size)]
    
    cleaned_docs = []
    # Use more workers for parallel processing
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(64, len(batches))) as executor:
        process_batch = lambda batch: process_document_batch(batch, node_parser)
        futures = [executor.submit(process_batch, batch) for batch in batches]
        
        for future in tqdm(concurrent.futures.as_completed(futures), 
                         total=len(futures), 
                         desc="Processing documents"):
            cleaned_docs.extend(future.result())
    
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
        
        # Process embeddings in parallel
        Settings.num_output_threads = min(32, multiprocessing.cpu_count())
        
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

def create_enhanced_node_parser():
    # Create a multi-level chunking strategy with more granular levels
    chunking_levels = [
        # Level 1: Fine-grained chunks for precise retrieval
        {"chunk_size": CONFIG['chunk_size'], "chunk_overlap": CONFIG['chunk_overlap']},
        # Level 2: Sentence-level chunks
        {"chunk_size": CONFIG['chunk_size'] * 2, "chunk_overlap": CONFIG['chunk_overlap'] * 2},
        # Level 3: Paragraph-level chunks
        {"chunk_size": CONFIG['chunk_size'] * 4, "chunk_overlap": CONFIG['chunk_overlap'] * 3},
        # Level 4: Section-level chunks
        {"chunk_size": CONFIG['chunk_size'] * 8, "chunk_overlap": CONFIG['chunk_overlap'] * 4}
    ]
    
    return HierarchicalNodeParser.from_defaults(
        chunk_sizes=[level["chunk_size"] for level in chunking_levels],
        include_metadata=True,
        include_prev_next_rel=True
    )

def detect_semantic_sections(text):
    # Use regex patterns to identify section types based on common patterns
    patterns = {
        'introduction': r'\b(introduction|background|overview)\b',
        'methodology': r'\b(method|methodology|procedure|protocol)\b',
        'results': r'\b(results|findings|outcomes)\b',
        'discussion': r'\b(discussion|analysis|interpretation)\b',
        'conclusion': r'\b(conclusion|summary|final)\b',
        'abstract': r'\b(abstract|summary)\b',
        'clinical_findings': r'\b(clinical|patient|treatment)\b',
        'statistical_analysis': r'\b(statistical|analysis|significance|p-value)\b'
    }
    
    # Check each pattern and calculate confidence based on word frequency
    matches = {}
    text_lower = text.lower()
    total_matches = 0
    
    for section, pattern in patterns.items():
        count = len(re.findall(pattern, text_lower))
        matches[section] = count
        total_matches += count
    
    # Sort sections by match count
    sorted_sections = sorted(matches.items(), key=lambda x: x[1], reverse=True)
    
    # Calculate confidence scores (normalized)
    total_matches = max(total_matches, 1)  # Avoid division by zero
    result = {
        'primary_section': sorted_sections[0][0],
        'primary_confidence': sorted_sections[0][1] / total_matches,
        'secondary_section': sorted_sections[1][0] if len(sorted_sections) > 1 else 'unknown',
        'secondary_confidence': sorted_sections[1][1] / total_matches if len(sorted_sections) > 1 else 0.0,
        'tertiary_section': sorted_sections[2][0] if len(sorted_sections) > 2 else 'unknown',
        'tertiary_confidence': sorted_sections[2][1] / total_matches if len(sorted_sections) > 2 else 0.0
    }
    
    return result

if __name__ == "__main__":
    storage_context, config = setup()
    chat_session(storage_context)