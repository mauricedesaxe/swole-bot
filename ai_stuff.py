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
import openai

# TODO these things things could be improved:
# No feedback loop for response quality
# No reranking of retrieved documents
# No hybrid search (combining dense and sparse retrievals)
# No caching of common queries

SYSTEM_PROMPT = "You are a direct and helpful AI assistant with great expertise in sports medicine, weightlifting, and testosterone. Focus on providing clear, actionable information without adding disclaimers about consulting healthcare providers. Users are aware of when they need to seek professional help. Provide straightforward answers to questions while maintaining accuracy. Always provide sources for your answers. Always attempt to ask follow up questions to clarify your understanding of the user's question."

def setup():
    """Initializes the environment and loads configuration settings."""

    load_dotenv()
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_or_create_collection("my_collection")
    vector_store = ChromaVectorStore(chroma_collection=collection)
    Settings.llm = OpenAI(
        model="gpt-4o-mini",
        temperature=0.0,
        system_prompt=SYSTEM_PROMPT,
        output_formatter=lambda response, nodes: (
            f"{response}\n\nSources:\n" + 
            "\n".join([f"- {node.metadata['source']}" for node in nodes])
        ),
        response_mode="tree_summarize",
        streaming=True,
    )
    return StorageContext.from_defaults(vector_store=vector_store)

def chat_session(storage_context):
    """Starts a chat session with the user."""

    if not os.path.exists("data") or not os.listdir("data"):
        print("No data found. Please run 'make scrape' first.")
        return
    
    chroma_collection = storage_context.vector_store._collection
    collection_count = chroma_collection.count()
    
    if collection_count == 0:
        print("Creating new index...")
        documents = process_documents("data", 50)
        Settings.num_output_threads = min(32, multiprocessing.cpu_count())
        index = VectorStoreIndex.from_documents(documents, storage_context=storage_context, show_progress=True)
    else:
        print("Loading existing index...")
        try:
            index = VectorStoreIndex.from_vector_store(storage_context.vector_store)
        except Exception as e:
            print(f"Error loading existing index: {str(e)}")
            print("Creating new index instead...")
            documents = process_documents("data", 50)
            index = VectorStoreIndex.from_documents(documents, storage_context=storage_context, show_progress=True)

    chat_engine = index.as_chat_engine(
        chat_mode="context",
        verbose=True,
        system_prompt=SYSTEM_PROMPT,
        node_relationships=True,
        similarity_top_k=5,
        context_window=4096,
        output_formatter=lambda response, nodes: (
            f"{response}\n\nSources:\n" + 
            "\n".join([f"- {node.metadata['source']}" for node in nodes])
        ),
        include_source_metadata=True,
        response_mode="tree_summarize",
        streaming=True,
    )
    print("\nChat session started. Type 'exit' to end.")

    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ['exit', 'quit']:
            break
        print("\nAssistant:", chat_engine.chat(user_input).response)

def process_documents(directory, batch_size):
    """Processes documents in the specified directory."""

    reader = SimpleDirectoryReader(input_dir=directory, recursive=False)
    documents = reader.load_data()
    node_parser = create_enhanced_node_parser()
    batch_size = max(1, min(batch_size, len(documents)))
    batches = [documents[i:i + batch_size] for i in range(0, len(documents), batch_size)]
    
    cleaned_docs = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(64, len(batches))) as executor:
        futures = [executor.submit(process_document_batch, batch, node_parser) for batch in batches]
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Processing documents"):
            cleaned_docs.extend(future.result())
    
    return cleaned_docs

def create_enhanced_node_parser():
    """Creates a multi-level chunking strategy with more granular levels."""

    chunking_levels = [
        {"chunk_size": 1024, "chunk_overlap": 256},
        {"chunk_size": 1024 * 2, "chunk_overlap": 256 * 2},
        {"chunk_size": 1024 * 4, "chunk_overlap": 256 * 3},
        {"chunk_size": 1024 * 8, "chunk_overlap": 256 * 4},
    ]
    
    return HierarchicalNodeParser.from_defaults(
        chunk_sizes=[level["chunk_size"] for level in chunking_levels],
        include_metadata=True,
        include_prev_next_rel=True,
    )

def process_document_batch(batch, node_parser):
    """Processes a single batch of documents."""

    batch_docs = [
        Document(
            text=doc.text,
            metadata={**extract_metadata(doc.text), "source": doc.metadata.get("file_path", "")}
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

def extract_metadata(text):
    """Extracts metadata from the input text using OpenAI's LLM for enhanced classification."""

    # Basic metadata extraction
    basic_metadata = {
        'processed_date': datetime.now().isoformat(),
        'word_count': len(text.split()),
        'char_count': len(text),
        'sentences': len(re.split(r'[.!?]+', text)),
        'has_numbers': bool(re.search(r'\d', text)),
        'has_citations': bool(re.search(r'\[\d+\]|\(\d{4}\)', text)),
    }

    # Use OpenAI to classify the text and extract additional metadata
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": f"Analyze the following text and provide relevant metadata such as themes, tone, and potential categories:\n\n{text}"}
            ],
            max_tokens=150
        )
        llm_metadata = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error while calling OpenAI API: {e}")
        llm_metadata = "Unable to extract LLM metadata"

    return {**basic_metadata, 'llm_metadata': llm_metadata}

def detect_semantic_sections(text):
    """Detects semantic sections in the text using OpenAI for improved accuracy."""
    
    # Use OpenAI to analyze the text and suggest semantic sections
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": f"Analyze the following text and identify its semantic sections, considering it may include medical studies, fitness blog articles, or sports literature:\n\n{text}"}
            ],
            max_tokens=150
        )
        semantic_sections = response.choices[0].message.content.strip().split('\n')
        
        # Parse the response into a structured format
        sections = {}
        for section in semantic_sections:
            if ':' in section:
                key, value = section.split(':', 1)
                sections[key.strip().lower()] = value.strip()
        
        # Calculate confidence based on the presence of sections
        total_matches = len(sections) or 1  # Avoid division by zero
        return {
            'primary_section': list(sections.keys())[0] if sections else 'unknown',
            'primary_confidence': 1.0 / total_matches,
            'secondary_section': list(sections.keys())[1] if len(sections) > 1 else 'unknown',
            'secondary_confidence': 1.0 / total_matches if len(sections) > 1 else 0.0,
            'tertiary_section': list(sections.keys())[2] if len(sections) > 2 else 'unknown',
            'tertiary_confidence': 1.0 / total_matches if len(sections) > 2 else 0.0,
        }
    except Exception as e:
        print(f"Error while calling OpenAI API: {e}")
        return {
            'primary_section': 'unknown',
            'primary_confidence': 0.0,
            'secondary_section': 'unknown',
            'secondary_confidence': 0.0,
            'tertiary_section': 'unknown',
            'tertiary_confidence': 0.0,
        }

if __name__ == "__main__":
    storage_context = setup()
    chat_session(storage_context)