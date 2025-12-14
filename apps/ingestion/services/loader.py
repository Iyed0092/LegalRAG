import uuid
from .pdf_parser import extract_text_from_pdf
from .chunker import split_text_into_chunks
from apps.rag_engine.connectors.vector_store import VectorStoreClient
from apps.rag_engine.connectors.graph_store import GraphStoreClient

def process_document(file_path, doc_title):
    print(f"\n DEBUG INGESTION : Début du traitement de {doc_title}")
    
    # 1. Extraction
    try:
        raw_text = extract_text_from_pdf(file_path)
        print(f"DEBUG : Taille du texte extrait : {len(raw_text)} caractères")
    except Exception as e:
        print(f"ERREUR CRITIQUE lors de la lecture du PDF : {e}")
        return
    
    if len(raw_text) < 50:
        print(" CRITIQUE : Le texte extrait est vide ou trop court ! (PDF scanné ?)")
        return # On arrête tout
    else:
        print(f"Extrait (début) : {raw_text[:100]}...")

    # 2. Chunking
    chunks = split_text_into_chunks(raw_text)
    print(f"DEBUG : Nombre de morceaux (chunks) créés : {len(chunks)}")

    vector_client = VectorStoreClient()
    graph_client = GraphStoreClient()

    ids = []
    documents = []
    metadatas = []

    for i, chunk in enumerate(chunks):
        chunk_id = str(uuid.uuid4())
        ids.append(chunk_id)
        documents.append(chunk)
        metadatas.append({
            "source": doc_title,
            "chunk_index": i
        })
        
        try:
            graph_client.create_article_node(
                article_id=chunk_id,
                title=f"{doc_title} - Part {i}",
                content_summary=chunk[:100]
            )
        except Exception as e:
            print(f"Erreur Graph (non critique) : {e}")

    if documents:
        print(f"DEBUG : Envoi de {len(documents)} vecteurs vers ChromaDB...")
        try:
            vector_client.add_documents(documents, metadatas, ids)
            print("SUCCÈS : Vecteurs enregistrés !")
        except Exception as e:
            print(f" ERREUR ChromaDB : {e}")
    else:
        print("ALERTE : Aucun document à enregistrer.")