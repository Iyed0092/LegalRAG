from typing import List, Optional
import torch
import logging
from langchain_community.retrievers import BM25Retriever
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from sentence_transformers import CrossEncoder
from apps.rag_engine.connectors.vector_store import VectorStoreClient
from apps.rag_engine.connectors.graph_store import GraphStoreClient

logger = logging.getLogger(__name__)

class EnsembleRetriever(BaseRetriever):
    retrievers: List[BaseRetriever]
    weights: List[float]

    def _get_relevant_documents(self, query: str, *, run_manager: CallbackManagerForRetrieverRun = None) -> List[Document]:
        all_docs_list = []
        for retriever in self.retrievers:
            if run_manager:
                docs = retriever.invoke(query, config={"callbacks": run_manager.get_child()})
            else:
                docs = retriever.invoke(query)
            all_docs_list.append(docs)

        unique_docs = {}
        for docs in all_docs_list:
            for doc in docs:
                if doc.page_content not in unique_docs:
                    unique_docs[doc.page_content] = doc
        
        return list(unique_docs.values())

class HybridSearcher:
    def __init__(self):
        self.vector_connector = VectorStoreClient()
        self.chroma_db = self.vector_connector.db
        self.graph_client = GraphStoreClient()
        logger.info(" Loading Cross-Encoder model on GPU...")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.reranker = CrossEncoder(
            'cross-encoder/ms-marco-MiniLM-L-6-v2',
            device=device
        )

        if device == "cuda" and torch.cuda.is_bf16_supported():
            self.reranker.model.to(dtype=torch.bfloat16)
            logger.info(f"Cross-Encoder running on {torch.cuda.get_device_name(0)} (Mode: Bfloat16 ).")
        else:
            logger.info(f"Cross-Encoder running on {device} (Mode: Standard).")
                

    def search_and_rerank(self, query: str, initial_k: int = 20, final_k: int = 5) -> List[Document]:
        vector_retriever = self.chroma_db.as_retriever(search_kwargs={"k": initial_k})
        collection_data = self.chroma_db.get()
        all_texts = collection_data['documents']
        if not all_texts:
            logger.warning("Database is empty.")
            return []

        bm25_retriever = BM25Retriever.from_texts(all_texts)
        bm25_retriever.k = initial_k
        ensemble = EnsembleRetriever(
            retrievers=[bm25_retriever, vector_retriever],
            weights=[0.5, 0.5]
        )
        
        candidates = ensemble.invoke(query)
        logger.info(f"Hybrid Phase: Found {len(candidates)} candidates.")
        found_sources = list(set([d.metadata.get('source') for d in candidates if d.metadata.get('source')]))
        graph_context_str = ""
        if found_sources:
            graph_context_str = self.graph_client.get_graph_context(found_sources)
            if graph_context_str:
                logger.info(f"Graph Phase: Retrieved context for {len(found_sources)} documents.")
            
        if not candidates or not self.reranker:
            return candidates[:final_k]

        pairs = [[query, doc.page_content] for doc in candidates]
        scores = self.reranker.predict(pairs)
        doc_scores = list(zip(candidates, scores))
        doc_scores.sort(key=lambda x: x[1], reverse=True)

        top_docs = []
        for i, (doc, score) in enumerate(doc_scores[:final_k]):
            doc.metadata["relevance_score"] = float(score)
            doc.metadata["rank"] = i + 1
            if i == 0 and graph_context_str:
                doc.metadata["graph_context"] = graph_context_str
                
            top_docs.append(doc)
            logger.info(f"Rank {i+1} | Score: {score:.4f} | Src: {doc.metadata.get('source', 'Unknown')}")

        return top_docs