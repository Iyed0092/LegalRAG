import logging
import torch
import chromadb
from chromadb.config import Settings
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from django.conf import settings

logger = logging.getLogger(__name__)

class VectorStoreClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorStoreClient, cls).__new__(cls)
            
            persist_path = getattr(settings, 'CHROMA_DB_PATH', './data/chroma_db')
            collection_name = getattr(settings, 'CHROMA_COLLECTION_NAME', 'legal_docs')
            model_name = getattr(settings, 'EMBEDDING_MODEL_NAME', 'all-MiniLM-L6-v2')

            logger.info(f"Initializing Vector Store at {persist_path}...")
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model_kwargs = {"device": device, "trust_remote_code": True}
            
            # Optimisation RTX 4060
            if device == "cuda" and torch.cuda.is_bf16_supported():
                model_kwargs["model_kwargs"] = {"torch_dtype": torch.bfloat16}
                logger.info(f"VectorStore: Embeddings running on {device} (Bfloat16 Mode).")
            else:
                logger.info(f"VectorStore: Embeddings running on {device}.")


            cls._instance.embedding_fn = HuggingFaceEmbeddings(
                model_name=model_name,
                model_kwargs=model_kwargs,
                encode_kwargs={"device": device, "batch_size": 32}
            )

            cls._instance.client = chromadb.PersistentClient(
                path=persist_path,
                settings=Settings(anonymized_telemetry=False)
            )
            cls._instance.db = Chroma(
                client=cls._instance.client,
                collection_name=collection_name,
                embedding_function=cls._instance.embedding_fn,
            )
            
        return cls._instance

    def get_collection(self):
        return self.client.get_collection(
            name=getattr(settings, 'CHROMA_COLLECTION_NAME', 'legal_docs')
        )


    def add_documents(self, documents, metadatas, ids):
        self.db.add_texts(
            texts=documents,
            metadatas=metadatas,
            ids=ids
        )

    def search(self, query, n_results=5):
        return self.db.similarity_search(query, k=n_results)