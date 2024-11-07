import os
from datetime import datetime
import chromadb
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    Settings,
)
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.chroma.base import ChromaVectorStore
from llama_index.core.schema import Document
from dotenv import load_dotenv
import re
from llama_index.core.node_parser import HierarchicalNodeParser
import concurrent.futures
from tqdm import tqdm
import multiprocessing
from config import CONFIG

def setup():
    """Initializes the environment and loads configuration settings."""
    load_dotenv()
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_or_create_collection("my_collection")
    vector_store = ChromaVectorStore(chroma_collection=collection)
    Settings.llm = OpenAI(
        model=CONFIG['model'],
        temperature=CONFIG['temperature'],
        system_prompt=CONFIG['system_prompt'],
    )
    return StorageContext.from_defaults(vector_store=vector_store)

def clean_text(text):
    """Preserves medical terminology, units, and measurements while cleaning text."""
    # Preserve common medical/fitness units and measurements
    text = re.sub(r'(\d+)(?:\s*)(mg|kg|lb|g|ml|ng|dl|pmol|nmol|iu|cc|mcg)', r'\1 \2', text)
    
    # Preserve common medical symbols
    text = re.sub(r'[^\w\s.,!?;:()\n\-\[\]"\'$%±<>°→←↔️∆/]', ' ', text)
    
    # Normalize whitespace while preserving sentence structure
    text = ' '.join(text.split())
    
    # Standardize unit formatting
    text = re.sub(r'(\d+)\s*(mg|kg|lb|g|ml|ng|dl|pmol|nmol|iu|cc|mcg)', r'\1\2', text)
    
    return text

def extract_metadata(text):
    """Extracts metadata from the input text."""
    return {
        'processed_date': datetime.now().isoformat(),
        'word_count': len(text.split()),
        'char_count': len(text),
        'sentences': len(re.split(r'[.!?]+', text)),
        'has_numbers': bool(re.search(r'\d', text)),
        'has_citations': bool(re.search(r'\[\d+\]|\(\d{4}\)', text)),
    }

def process_document_batch(batch, node_parser):
    """Processes a single batch of documents."""
    batch_docs = [
        Document(
            text=clean_text(doc.text),
            metadata={**extract_metadata(clean_text(doc.text)), "source": doc.metadata.get("file_path", "")}
        )
        for doc in batch
    ]
    
    nodes = node_parser.get_nodes_from_documents(batch_docs)
    return [
        Document(
            text=node.text,
            metadata={
                **doc.metadata,
                **node.metadata,
                **detect_semantic_sections(node.text),
                'chunk_index': i,
                'total_chunks': len(nodes),
                'level': node.metadata.get('level', 0),
                'next_chunk_id': node.relationships.get('next'),
                'prev_chunk_id': node.relationships.get('previous'),
            }
        )
        for i, (doc, node) in enumerate(zip(batch_docs, nodes))
    ]

def process_documents(directory, batch_size):
    """Processes documents in the specified directory."""
    reader = SimpleDirectoryReader(input_dir=directory, recursive=False)
    documents = reader.load_data()
    node_parser = create_enhanced_node_parser()
    batch_size = min(batch_size, len(documents))
    batches = [documents[i:i + batch_size] for i in range(0, len(documents), batch_size)]
    
    cleaned_docs = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(64, len(batches))) as executor:
        futures = [executor.submit(process_document_batch, batch, node_parser) for batch in batches]
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Processing documents"):
            cleaned_docs.extend(future.result())
    
    return cleaned_docs

def chat_session(storage_context):
    """Starts a chat session with the user."""
    if not os.path.exists("data") or not os.listdir("data"):
        print("No data found. Please run 'make scrape' first.")
        return
    
    chroma_collection = storage_context.vector_store._collection
    collection_count = chroma_collection.count()
    
    if collection_count == 0:
        print("Creating new index...")
        documents = process_documents("data", CONFIG['batch_size'])
        Settings.num_output_threads = min(32, multiprocessing.cpu_count())
        index = VectorStoreIndex.from_documents(documents, storage_context=storage_context, show_progress=True)
    else:
        print("Loading existing index...")
        try:
            index = VectorStoreIndex.from_vector_store(storage_context.vector_store)
        except Exception as e:
            print(f"Error loading existing index: {str(e)}")
            print("Creating new index instead...")
            documents = process_documents("data", CONFIG['batch_size'])
            index = VectorStoreIndex.from_documents(documents, storage_context=storage_context, show_progress=True)

    chat_engine = index.as_chat_engine(
        chat_mode="context",
        verbose=True,
        system_prompt=CONFIG['system_prompt'],
        node_relationships=True,
        similarity_top_k=5,
        context_window=4096,
    )
    print("\nChat session started. Type 'exit' to end.")

    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ['exit', 'quit']:
            break
        print("\nAssistant:", chat_engine.chat(user_input).response)

def create_enhanced_node_parser():
    """Creates a multi-level chunking strategy with more granular levels."""
    chunking_levels = [
        {"chunk_size": CONFIG['chunk_size'], "chunk_overlap": CONFIG['chunk_overlap']},
        {"chunk_size": CONFIG['chunk_size'] * 2, "chunk_overlap": CONFIG['chunk_overlap'] * 2},
        {"chunk_size": CONFIG['chunk_size'] * 4, "chunk_overlap": CONFIG['chunk_overlap'] * 3},
        {"chunk_size": CONFIG['chunk_size'] * 8, "chunk_overlap": CONFIG['chunk_overlap'] * 4},
    ]
    
    return HierarchicalNodeParser.from_defaults(
        chunk_sizes=[level["chunk_size"] for level in chunking_levels],
        include_metadata=True,
        include_prev_next_rel=True,
    )

def detect_semantic_sections(text):
    """Detects semantic sections in the text."""
    patterns = {
        'introduction': r'\b(introduction|background|overview)\b',
        'methodology': r'\b(method|methodology|procedure|protocol)\b',
        'results': r'\b(results|findings|outcomes)\b',
        'discussion': r'\b(discussion|analysis|interpretation)\b',
        'conclusion': r'\b(conclusion|summary|final)\b',
        'abstract': r'\b(abstract|summary)\b',
        'clinical_findings': r'\b(clinical|patient|treatment)\b',
        'statistical_analysis': r'\b(statistical|analysis|significance|p-value)\b',
    }
    
    matches = {section: len(re.findall(pattern, text.lower())) for section, pattern in patterns.items()}
    total_matches = sum(matches.values()) or 1  # Avoid division by zero
    sorted_sections = sorted(matches.items(), key=lambda x: x[1], reverse=True)
    
    return {
        'primary_section': sorted_sections[0][0],
        'primary_confidence': sorted_sections[0][1] / total_matches,
        'secondary_section': sorted_sections[1][0] if len(sorted_sections) > 1 else 'unknown',
        'secondary_confidence': sorted_sections[1][1] / total_matches if len(sorted_sections) > 1 else 0.0,
        'tertiary_section': sorted_sections[2][0] if len(sorted_sections) > 2 else 'unknown',
        'tertiary_confidence': sorted_sections[2][1] / total_matches if len(sorted_sections) > 2 else 0.0,
    }

if __name__ == "__main__":
    storage_context = setup()
    chat_session(storage_context)