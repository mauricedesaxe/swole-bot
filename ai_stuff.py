import os
from datetime import datetime
import chromadb
from llama_index import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    Settings,
)
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.schema import Document
import re
from llama_index.node_parser import HierarchicalNodeParser
import concurrent.futures
from tqdm import tqdm
import multiprocessing
from openai_helpers import make_openai_call
from llama_index.embeddings.jinaai import JinaEmbedding
from llama_index.postprocessor.jinaai_rerank import JinaRerank

SYSTEM_PROMPT = """You are an expert AI assistant specializing in testosterone, TRT, and sports medicine research. Follow these guidelines:

1. Response Structure:
- Ask clarifying questions
- Confirm understanding of user's question
- Provide a clear, direct answer
- Follow with supporting evidence
- End with relevant caveats or considerations

2. Source Integration:
- Cite specific studies when making claims
- Indicate the strength of evidence (e.g., meta-analysis vs. single study)
- Highlight any conflicting findings

3. Communication Style:
- Use precise medical terminology but explain complex concepts
- Be direct and clear about risks and benefits
- Avoid hedging language unless uncertainty is scientifically warranted

4. Follow-up:
- Identify gaps in the user's question that might need clarification
- Suggest related topics the user might want to explore
- Point out if more recent research might be available

Remember: Users are seeking expert knowledge. Focus on accuracy and clarity rather than general medical disclaimers which the users are already aware of."""

def setup():
    """Initializes the environment and loads configuration settings."""

    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_or_create_collection("my_collection")
    vector_store = ChromaVectorStore(chroma_collection=collection)
    Settings.llm = OpenAI(
        model="gpt-4o-mini",
        temperature=0.0,
        system_prompt=SYSTEM_PROMPT,
        logprobs=None,
        default_headers={},
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
    
    jina_embeddings = JinaEmbedding(api_key=os.getenv("JINA_API_KEY"), top_n=10)

    if collection_count == 0:
        print("Creating new index...")
        documents = process_documents("data", 50)
        Settings.num_output_threads = min(32, multiprocessing.cpu_count())
        index = VectorStoreIndex.from_documents(
            documents=documents,
            embed_model=jina_embeddings,
            storage_context=storage_context,
            show_progress=True
        )
    else:
        print("Loading existing index...")
        try:
            index = VectorStoreIndex.from_vector_store(
                storage_context.vector_store,
                embed_model=jina_embeddings
            )
        except Exception as e:
            print(f"Error loading existing index: {str(e)}")
            print("Creating new index instead...")
            documents = process_documents("data", 50)
            index = VectorStoreIndex.from_documents(
                documents=documents,
                embed_model=jina_embeddings,
                storage_context=storage_context,
                show_progress=True
            )

    jina_rerank = JinaRerank(api_key=os.getenv("JINA_API_KEY"), top_n=10)

    chat_engine = index.as_chat_engine(
        chat_mode="context",
        verbose=True,
        system_prompt=SYSTEM_PROMPT,
        node_relationships=True,
        similarity_top_k=10,
        node_postprocessors=[jina_rerank],
        context_window=4096,
        include_source_metadata=True,
        response_mode="tree_summarize",
        streaming=True
    )
    print("\nChat session started. Type 'exit' to end.")

    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ['exit', 'quit']:
            break
        
        print(f"\nSearching through {storage_context.vector_store._collection.count()} embeddings...")
        
        response = chat_engine.chat(user_input)
        
        source_nodes = []
        if hasattr(response, 'source_nodes'):
            source_nodes = response.source_nodes
            unique_sources = set()
            filtered_nodes = []
            for node in source_nodes:
                source = node.metadata.get('source', '')
                if source not in unique_sources:
                    unique_sources.add(source)
                    filtered_nodes.append(node)
            
            source_nodes = filtered_nodes
            print(f"\nFound {len(source_nodes)} unique source nodes")
            for i, node in enumerate(source_nodes):
                print(f"\nSource {i+1}:")
                print(f"Metadata: {node.metadata}")
        else:
            print("\nNo source_nodes attribute found in response")
            
        sources = [node.metadata.get('source', 'Unknown source') for node in source_nodes]
        formatted_response = f"{response.response}\n\nSources:\n" + "\n".join([f"- {source}" for source in sources])
        print("\nAssistant:", formatted_response)

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
    basic_metadata = {
        'processed_date': datetime.now().isoformat(),
        'word_count': len(text.split()),
        'char_count': len(text),
        'sentences': len(re.split(r'[.!?]+', text)),
        'has_numbers': bool(re.search(r'\d', text)),
        'has_citations': bool(re.search(r'\[\d+\]|\(\d{4}\)', text)),
    }
    return basic_metadata 

def detect_semantic_sections(text):
    """Detects semantic sections in the text using basic text analysis."""
    # Look for common section headers and keywords
    sections = []
    
    # Common medical/research paper sections
    if any(keyword in text.lower() for keyword in ['abstract', 'introduction', 'background']):
        sections.append('research_background')
    if any(keyword in text.lower() for keyword in ['method', 'procedure', 'protocol']):
        sections.append('methodology') 
    if any(keyword in text.lower() for keyword in ['result', 'finding', 'outcome']):
        sections.append('results')
    if any(keyword in text.lower() for keyword in ['discussion', 'conclusion']):
        sections.append('discussion')
        
    # Common fitness/sports content sections
    if any(keyword in text.lower() for keyword in ['workout', 'exercise', 'training']):
        sections.append('training')
    if any(keyword in text.lower() for keyword in ['diet', 'nutrition', 'supplement']):
        sections.append('nutrition')
    if any(keyword in text.lower() for keyword in ['dosage', 'protocol', 'cycle']):
        sections.append('protocol')

    # Medical condition sections
    if any(keyword in text.lower() for keyword in ['symptom', 'diagnosis', 'condition', 'disorder']):
        sections.append('medical_condition')
    if any(keyword in text.lower() for keyword in ['treatment', 'therapy', 'intervention']):
        sections.append('treatment')
    if any(keyword in text.lower() for keyword in ['side effect', 'adverse', 'risk']):
        sections.append('side_effects')
        
    # Research/evidence sections
    if any(keyword in text.lower() for keyword in ['study', 'trial', 'research', 'evidence']):
        sections.append('research')
    if any(keyword in text.lower() for keyword in ['meta-analysis', 'review', 'literature']):
        sections.append('meta_analysis')
    if any(keyword in text.lower() for keyword in ['mechanism', 'pathway', 'physiology']):
        sections.append('mechanism_of_action')
        
    # Ensure we have at least one section
    if not sections:
        sections.append('general')
        
    # Calculate confidence based on number of keyword matches
    total_matches = len(sections)
    
    return {
        'primary_section': sections[0] if sections else 'unknown',
        'primary_confidence': 1.0 / total_matches if sections else 0.0,
        'secondary_section': sections[1] if len(sections) > 1 else 'unknown',
        'secondary_confidence': 1.0 / total_matches if len(sections) > 1 else 0.0,
        'tertiary_section': sections[2] if len(sections) > 2 else 'unknown',
        'tertiary_confidence': 1.0 / total_matches if len(sections) > 2 else 0.0,
    }

if __name__ == "__main__":
    storage_context = setup()
    chat_session(storage_context)