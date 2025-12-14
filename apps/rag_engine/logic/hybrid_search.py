from apps.rag_engine.connectors.vector_store import VectorStoreClient
from apps.rag_engine.connectors.graph_store import GraphStoreClient
from apps.rag_engine.llm.flan_t5 import LLMService

class HybridRAGEngine:
    def __init__(self):
        self.vector_store = VectorStoreClient()
        self.graph_store = GraphStoreClient()
        self.llm_service = LLMService()

    def answer_question(self, question):
        vector_results = self.vector_store.search(question, n_results=10)
        
        vector_context = []
        retrieved_ids = []
        
        if vector_results and vector_results['documents']:
            for i, doc in enumerate(vector_results['documents'][0]):
                vector_context.append(doc)
                if vector_results['ids']:
                    retrieved_ids.append(vector_results['ids'][0][i])

        print("\n" + "="*40)
        print(f"RAG DEBUG - Question : {question}")
        print(f"Nombre de chunks trouvés : {len(vector_context)}")
        
        if len(vector_context) > 0:
            print(f"Contenu du 1er chunk (Aperçu) : {vector_context[0][:200]}...")
        else:
            print("ALERTE : Aucun chunk trouvé via la recherche vectorielle !")
            
        print("="*40 + "\n")

        graph_context = []
        for doc_id in retrieved_ids:
            related_nodes = self.graph_store.get_related_articles(doc_id)
            for node in related_nodes:
                graph_context.append(f"Related Article: {node.get('title', 'Unknown')}")

        full_context = "\n".join(vector_context + graph_context)

        if not full_context.strip():
            answer = "Information not found in the documents (Context was empty)."
        else:
            answer = self.llm_service.generate_answer(full_context, question)

        return {
            "question": question,
            "answer": answer,
            "sources": retrieved_ids,
            "context_used": full_context[:500] + "..." 
        }