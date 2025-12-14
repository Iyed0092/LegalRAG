import chromadb
from sentence_transformers import SentenceTransformer
from django.conf import settings

class VectorStoreClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorStoreClient, cls).__new__(cls)
            cls._instance.client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)
            cls._instance.collection = cls._instance.client.get_or_create_collection(
                name=settings.CHROMA_COLLECTION_NAME
            )
            cls._instance.model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        return cls._instance

    def add_documents(self, documents, metadatas, ids):
        embeddings = self.model.encode(documents).tolist()
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )

    def search(self, query, n_results=5):
        query_embedding = self.model.encode([query]).tolist()
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results
        )
        return results