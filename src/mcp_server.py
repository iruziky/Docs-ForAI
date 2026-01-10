import os
import json
import logging
from typing import Optional, Any
from dotenv import load_dotenv

from mcp.server.fastmcp import FastMCP

# Lazy imports will be done inside functions to speed up startup time.

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_server")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

mcp = FastMCP("Multi-Source Documentation Bot")

_embed_model = None
_reranker = None

def get_resources():
    global _embed_model, _reranker
    
    # Lazy imports to avoid heavy load at startup
    from llama_index.core import Settings
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    from llama_index.postprocessor.cohere_rerank import CohereRerank

    lancedb_uri = os.path.join(PROJECT_ROOT, "lancedb_data")

    if _embed_model is None:
        logger.info(f"Loading Embedding Model: all-MiniLM-L6-v2")
        _embed_model = HuggingFaceEmbedding(model_name="all-MiniLM-L6-v2")
        Settings.embed_model = _embed_model
        Settings.llm = None 

    if _reranker is None:
        cohere_key = os.getenv("COHERE_API_KEY")
        if cohere_key:
            logger.info("Initializing Cohere Reranker")
            _reranker = CohereRerank(api_key=cohere_key, top_n=4)
        else:
            logger.warning("COHERE_API_KEY missing. Reranking disabled.")
    
    return lancedb_uri, _embed_model, _reranker

def _search_lancedb(query: str, collection_name: str) -> str:
    """Vector search in LanceDB for a specific collection."""
    try:
        # Lazy imports for search functionality
        from llama_index.core import VectorStoreIndex, StorageContext, QueryBundle
        from llama_index.vector_stores.lancedb import LanceDBVectorStore
        
        lancedb_uri, _, reranker = get_resources()
        
        vector_store = LanceDBVectorStore(uri=lancedb_uri, table_name=collection_name)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        index = VectorStoreIndex.from_vector_store(
            vector_store,
            storage_context=storage_context
        )
        
        retriever = index.as_retriever(similarity_top_k=15)
        nodes = retriever.retrieve(query)
        
        if not nodes:
            return "No results found in this documentation."
            
        logger.info(f"[{collection_name}] Retrieved {len(nodes)} chunks.")
        
        if reranker:
            query_bundle = QueryBundle(query_str=query)
            reranked_nodes = reranker.postprocess_nodes(nodes, query_bundle=query_bundle)
        else:
            reranked_nodes = nodes[:4]
            
        final_texts = [node.get_content() for node in reranked_nodes]
        return "\n\n---\n\n".join(final_texts)
        
    except Exception as e:
        logger.error(f"Error in search ({collection_name}): {e}", exc_info=True)
        return f"Error processing search: {str(e)}"

def create_tool(config):
    """Creates a dynamic search tool for MCP."""
    collection = config["collection_name"]
    target_id = config["id"]
    desc = config.get("description", "Search documentation")
    
    def dynamic_search(query: str) -> str:
        return _search_lancedb(query, collection)
    
    dynamic_search.__name__ = f"search_{target_id}_docs"
    dynamic_search.__doc__ = desc
    return dynamic_search

def register_dynamic_tools():
    """Registers tools based on config.json."""
    config_path = os.path.join(PROJECT_ROOT, "config.json")
    if not os.path.exists(config_path):
        logger.error("config.json not found!")
        return

    logger.info(f"Reading configuration from: {os.path.abspath(config_path)}")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            configs = json.load(f)
    except Exception as e:
        logger.error(f"Error reading config.json: {e}")
        return

    logger.info(f"Found {len(configs)} tool configurations.")
        
    for config in configs:
        tool_func = create_tool(config)
        
        try:
            mcp.add_tool(tool_func)
            logger.info(f"Tool registered successfully: {tool_func.__name__}")
        except AttributeError:
            mcp.tool()(tool_func)

register_dynamic_tools()

def main():
    """Main entry point for the MCP server."""
    mcp.run()

if __name__ == "__main__":
    main()
