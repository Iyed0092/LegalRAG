from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from django.conf import settings
import os
import logging

from .logic.hybrid_search import HybridSearcher

logger = logging.getLogger(__name__)

class AskView(APIView):
    def post(self, request):
        question = request.data.get("question")
        if not question:
            return Response({"error": "Question is required"}, status=status.HTTP_400_BAD_REQUEST)

        logger.info(f"Processing query: {question}")
        searcher = HybridSearcher()
        
        docs = searcher.search_and_rerank(question, initial_k=20, final_k=5)
        
        if not docs:
            return Response({
                "answer": "Je n'ai trouvé aucun document pertinent dans la base de connaissances.",
                "sources": []
            })

        vector_context = "\n\n".join([
            f"[Document: {d.metadata.get('source', 'Unknown')} | Score: {d.metadata.get('relevance_score', 0):.2f}]\nContent: {d.page_content}" 
            for d in docs
        ])

        graph_context = ""
        if docs and "graph_context" in docs[0].metadata:
            graph_context = docs[0].metadata["graph_context"]
            logger.info("🕸️ Graph Context injected into prompt.")

        full_context = f"""
        --- EXCERPTS FROM DOCUMENTS (VECTOR SEARCH) ---
        {vector_context}

        --- KNOWLEDGE GRAPH INSIGHTS (STRUCTURE & RELATIONS) ---
        {graph_context}
        """
        sources = list(set([d.metadata.get('source', 'Unknown') for d in docs]))
        api_key = getattr(settings, 'GROQ_API_KEY', os.getenv('GROQ_API_KEY'))
        
        llm = ChatGroq(
            temperature=0, 
            model_name="llama-3.3-70b-versatile",
            api_key=api_key
        )

        template = """You are an expert Legal AI Assistant powered by a Graph-RAG system.
        
        Your goal is to answer the user's question accurately using the provided context.
        The context contains two parts:
        1. **Excerpts**: Text passages directly relevant to the question.
        2. **Graph Insights**: Information about document structure, dates, and related entities (Laws, Persons).

        Guidelines:
        - Synthesize information from both the text excerpts and the graph insights.
        - If the Graph Insights provide dates or document types, use them to contextualize your answer.
        - Cite specific documents (e.g., "According to the Labor Code...").
        - If the answer is not in the context, say "I don't have enough information."
        
        Context:
        {context}
        
        Question: {question}
        
        Answer:"""

        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | llm | StrOutputParser()

        logger.info("Generating answer...")
        answer = chain.invoke({"context": full_context, "question": question})

        return Response({
            "answer": answer,
            "sources": sources,
            "graph_context_used": bool(graph_context)
        })
