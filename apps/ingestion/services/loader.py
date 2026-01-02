import os
import uuid
import logging
from datetime import datetime
from langchain_community.document_loaders import PDFMinerLoader
from apps.ingestion.services.chunker import process_document
from apps.rag_engine.connectors.vector_store import VectorStoreClient
from apps.rag_engine.connectors.graph_store import GraphStoreClient

logger = logging.getLogger(__name__)

class DocumentLoader:
    def __init__(self):
        self.vector_client = VectorStoreClient()
        self.graph_client = GraphStoreClient()

    def process_and_load(self, file_path: str, original_filename: str):
        try:
            logger.info(f"Starting ingestion for: {original_filename}")
            loader = PDFMinerLoader(file_path)
            pages = loader.load()
            full_text = "\n\n".join([p.page_content for p in pages])

            print(f"[DEBUG EXTRACTION] Taille totale du texte extrait : {len(full_text)}")
            if len(full_text) > 200:
                print(f"[DEBUG EXTRACTION] Aperçu (début) : \n---\n{full_text[:200]}\n---")
            else:
                print(f"[DEBUG EXTRACTION] TEXTE TROP COURT OU VIDE : '{full_text}'")

            logger.info(f"Extracted Text Length: {len(full_text)} characters.")

            if not full_text.strip() or len(full_text) < 100:
                logger.warning(f"PDF seems empty, scanned (image only), or encrypted: {original_filename}")
                return False

            self.graph_client.create_document_node(
                file_name=original_filename,
                upload_date=datetime.now().isoformat(),
                metadata={"page_count": len(pages)}
            )

            logger.info("Sending text to Semantic Chunker & Graph Extractor...")
            chunks_data = process_document(full_text, filename=original_filename)
            logger.info(f"Obtained {len(chunks_data)} enriched items. Saving to Neo4j & Chroma...")
            ids = []
            metadatas = []
            documents_for_chroma = []
            print(f"DEBUG: Entering loop for {len(chunks_data)} chunks...")

            for i, item in enumerate(chunks_data):
                if isinstance(item, dict):
                    chunk_text = item.get("text_content", "")
                    entities = item.get("entities", [])
                else:
                    chunk_text = str(item)
                    entities = []

                chunk_id = f"{original_filename}_{uuid.uuid4().hex[:8]}"
                ids.append(chunk_id)
                metadatas.append({
                    "source": original_filename,
                    "chunk_index": i,
                    "type": "enriched_chunk"
                })
                documents_for_chroma.append(chunk_text)
                self.graph_client.add_chunk_node(
                    file_name=original_filename,
                    chunk_text=chunk_text,
                    chunk_id=chunk_id,
                    chunk_index=i
                )

                if entities:
                    for ent in entities:
                        # ent like {'name': 'Article 12', 'type': 'LAW'}
                        self.graph_client.create_entity_and_relate(
                            chunk_id=chunk_id,
                            entity_name=ent.get('name'),
                            entity_type=ent.get('type', 'Entity')
                        )
            if documents_for_chroma:
                collection = self.vector_client.get_collection()
                collection.add(
                    documents=documents_for_chroma,
                    metadatas=metadatas,
                    ids=ids
                )

            logger.info(f"Successfully ingested {original_filename} ({len(chunks_data)} chunks + Entities)")
            return True

        except Exception as e:
            logger.error(f"Error processing file {original_filename}: {e}", exc_info=True)
            return False
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info("Temporary file cleaned up.")
                