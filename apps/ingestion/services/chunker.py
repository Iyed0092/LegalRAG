import time
import logging
import torch
import json
import re
import os
import concurrent.futures
from functools import partial
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_models import ChatOllama
from tqdm import tqdm

logger = logging.getLogger(__name__)

def get_device_config():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model_kwargs = {"device": device, "trust_remote_code": True}
    encode_kwargs = {"device": device, "batch_size": 32}

    if device == "cuda" and torch.cuda.is_bf16_supported():
        logger.info("GPU Acceleration: Bfloat16 enabled (RTX 4060 Optimized).")
        model_kwargs["model_kwargs"] = {"torch_dtype": torch.bfloat16}
    else:
        logger.info(f"GPU Acceleration: Standard Precision on {device}.")
    return model_kwargs, encode_kwargs


def split_text_into_chunks_recursive(text, chunk_size=1200, chunk_overlap=200):
    logger.warning("Fallback: Using Recursive Character Splitter.")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return text_splitter.split_text(text)

def split_text_semantically(text, threshold=95):
    if len(text) < 1000: return [text]
    model_kwargs, encode_kwargs = get_device_config()
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs
    )
    text_splitter = SemanticChunker(
        embeddings, 
        breakpoint_threshold_type="percentile", 
        breakpoint_threshold_amount=threshold
    )
    docs = text_splitter.create_documents([text])
    chunks = [d.page_content for d in docs]
    
    if len(text) > 5000 and len(chunks) < 3:
        return split_text_into_chunks_recursive(text)
    
    logger.info(f"Semantic Splitter success: {len(chunks)} chunks.")
    return chunks



def _process_single_chunk_graph(chunk_data):
    chunk, chain, doc_summary = chunk_data
    if len(chunk) < 40:
        return {"text_content": chunk, "entities": []}


    response_json_str = chain.invoke({
        "doc_context": doc_summary,
        "chunk_content": chunk
    })
    
    json_match = re.search(r"\{.*\}", response_json_str, re.DOTALL)
    if json_match:
        data = json.loads(json_match.group(0))
        
        context = data.get("context", "General context.")
        entities = data.get("entities", [])
        
        clean_entities = []
        if isinstance(entities, list):
            for ent in entities:
                if isinstance(ent, dict) and "name" in ent:
                    clean_entities.append(ent)
        enriched_text = f"Context: {context}\n\nContent: {chunk}"
        
        return {
            "text_content": enriched_text,
            "entities": clean_entities
        }
    
    return {"text_content": chunk, "entities": []}

def enrich_and_extract_graph(chunks, full_document_text):
    if not chunks: return []

    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
    llm = ChatOllama(
        model="mistral-nemo",
        temperature=0,
        base_url=ollama_url,
        format="json"
    )

    prompt = ChatPromptTemplate.from_template(
        """
        You are an expert at Knowledge Graph Extraction. Analyze this document chunk.
        
        <global_document_context>
        {doc_context}
        </global_document_context>

        <chunk_to_analyze>
        {chunk_content}
        </chunk_to_analyze>

        TASK:
        1. Summarize the role of this chunk within the document in 1 short sentence.
        2. Extract key entities: Financial Concepts (Asset, Liability, etc.), Persons, or Laws.

        Return ONLY a JSON object:
        {{
            "context": "Short summary here",
            "entities": [
                {{"name": "EntityName", "type": "TYPE"}}
            ]
        }}
        """
    )
    
    chain = prompt | llm | StrOutputParser()
    doc_summary = full_document_text[:1500] + "..."
    work_items = [(chunk, chain, doc_summary) for chunk in chunks]
    max_workers = 2 if torch.cuda.is_available() else 4
    
    print(f"Starting Contextual Enrichment & Graph Extraction (Workers: {max_workers})...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(tqdm(
            executor.map(_process_single_chunk_graph, work_items),
            total=len(chunks),
            desc="Analyzing Chunks",
            unit="chunk"
        ))

    return results


def process_document(text, filename=None, **kwargs):
    print(f"Processing document: {filename or 'Unknown'}")
    raw_chunks = split_text_semantically(text)
    enriched_data = enrich_and_extract_graph(raw_chunks, text)
    return enriched_data