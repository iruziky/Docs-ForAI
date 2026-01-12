import os
import sys
import logging
import json
import argparse
from typing import List
from dotenv import load_dotenv
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    Settings,
    Document
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.lancedb import LanceDBVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

try:
    from scraper import scrape
except ImportError:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from scraper import scrape

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_text(text: str) -> str:
    """Normalize spaces and line breaks in the text."""
    if not text:
        return ""
    cleaned = " ".join(text.split())
    return cleaned

def clean_documents(documents: List[Document]) -> List[Document]:
    """Apply cleaning to all documents while preserving metadata."""
    cleaned_docs = []
    for doc in documents:
        cleaned_msg = clean_text(doc.text)
        if cleaned_msg:
            new_doc = Document(
                text=cleaned_msg,
                metadata=doc.metadata,
                excluded_embed_metadata_keys=doc.excluded_embed_metadata_keys,
                excluded_llm_metadata_keys=doc.excluded_llm_metadata_keys,
                relationships=doc.relationships
            )
            cleaned_docs.append(new_doc)
    return cleaned_docs

CACHE_FILE = "ingestion_cache.json"

def load_cache() -> set:
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        except Exception as e:
            logger.warning(f"Error reading cache: {e}. Starting empty.")
            return set()
    return set()

def save_cache(cache: set):
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(list(cache), f, indent=2)
    except Exception as e:
        logger.error(f"Error saving cache: {e}")

def process_target(config: dict, base_docs_dir: str = "docs_input") -> bool:
    target_id = config.get("id")
    name = config.get("name")
    base_url = config.get("base_url")
    start_url = config.get("start_url")
    output_folder = config.get("output_folder")
    collection_name = config.get("collection_name")
    
    logger.info(f"\n>>> Processing: {name} ({target_id}) <<<")
    
    target_dir = os.path.join(base_docs_dir, output_folder)
    
    # 1. SCRAPING
    logger.info(f"Starting Scraping of {base_url} to {target_dir}...")
    try:
        scrape(base_url, target_dir, make_subdir=False, start_url=start_url)
    except Exception as e:
        logger.error(f"Failed to scrape {name}: {e}")
    
    if not os.path.exists(target_dir):
        logger.error(f"Directory {target_dir} does not exist. Skipping.")
        return False

    # 2. VECTORIZATION / INGESTION
    lancedb_uri = "./lancedb_data"
    logger.info(f"Using LanceDB at: {lancedb_uri}, Table: {collection_name}")
    
    vector_store = LanceDBVectorStore(
        uri=lancedb_uri,
        table_name=collection_name,
        mode="overwrite"
    )
    
    logger.info("Loading embedding model: all-MiniLM-L6-v2")
    embed_model = HuggingFaceEmbedding(model_name="all-MiniLM-L6-v2")
    
    text_splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)
    
    Settings.embed_model = embed_model
    Settings.text_splitter = text_splitter
    
    logger.info("Loading documents from disk...")
    reader = SimpleDirectoryReader(input_dir=target_dir, recursive=True)
    documents = reader.load_data()
    logger.info(f"Documents loaded: {len(documents)}")
    
    if not documents:
        logger.warning("No documents found. Skipping vectorization.")
        return False

    documents = clean_documents(documents)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    
    logger.info(f"Indexing documents in collection '{collection_name}'...")
    try:
        VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
            show_progress=True
        )
        logger.info(f"Successfully indexed {name}!")
        return True
    except Exception as e:
        logger.error(f"Error indexing {name}: {e}")
        return False

def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Config-Driven Document Ingestion")
    parser.add_argument("--target_id", type=str, help="ID of the specific configuration to process")
    parser.add_argument("--config", type=str, default="config.json", help="Path to the config.json file")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.config):
        logger.error(f"Configuration file not found: {args.config}")
        sys.exit(1)
        
    with open(args.config, 'r', encoding='utf-8') as f:
        configs = json.load(f)
        
    targets_to_process = []
    
    if args.target_id:
        targets_to_process = [c for c in configs if c['id'] == args.target_id]
        if not targets_to_process:
            logger.error(f"Target ID '{args.target_id}' not found in config.")
            sys.exit(1)
    else:
        targets_to_process = configs
        
    logger.info(f"Found {len(targets_to_process)} targets to process.")
    
    cache = load_cache()
    
    for config in targets_to_process:
        t_id = config.get("id")
        
        if t_id in cache:
            logger.info(f"Target '{t_id}' found in cache. Skipping.")
            continue
            
        success = process_target(config)
        
        if success:
            logger.info(f"Adding '{t_id}' to cache.")
            cache.add(t_id)
            save_cache(cache)

if __name__ == "__main__":
    main()
