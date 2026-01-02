import logging
import os
from neo4j import GraphDatabase
from langchain_community.graphs import Neo4jGraph
from django.conf import settings

logger = logging.getLogger(__name__)

class GraphStoreClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GraphStoreClient, cls).__new__(cls)
            uri = getattr(settings, 'NEO4J_URI', os.getenv('NEO4J_URI', 'bolt://localhost:7687'))
            user = getattr(settings, 'NEO4J_USERNAME', os.getenv('NEO4J_USERNAME', 'neo4j'))
            password = getattr(settings, 'NEO4J_PASSWORD', os.getenv('NEO4J_PASSWORD', 'password'))
            cls._instance.driver = GraphDatabase.driver(uri, auth=(user, password))
            cls._instance.driver.verify_connectivity()
            logger.info("Neo4j Native Driver Connected successfully.")
            cls._instance.graph = Neo4jGraph(
                url=uri, 
                username=user, 
                password=password
            )
            logger.info("LangChain Graph Adapter Initialized.")
            

        return cls._instance

    def close(self):
        if self.driver:
            self.driver.close()

    def create_document_node(self, file_name: str, metadata: dict = None, upload_date=None, **kwargs):
        if not self.driver:
            logger.error("Neo4j driver not available. Skipping node creation.")
            return

        query = """
        MERGE (d:Document {name: $file_name})
        ON CREATE SET 
            d.created_at = datetime(), 
            d.status = 'ingested',
            d.upload_date = $upload_date,
            d.source_type = 'pdf'
        RETURN d
        """
        date_str = str(upload_date) if upload_date else "Unknown"
        with self.driver.session() as session:
            session.run(query, file_name=file_name, upload_date=date_str)
            logger.info(f"📄 Graph Node created/merged for: {file_name}")
    

    def add_chunk_node(self, file_name: str, chunk_text: str, chunk_id: str, chunk_index: int = 0, **kwargs):
        if not self.driver: return

        query = """
        MERGE (d:Document {name: $file_name})
        MERGE (c:Chunk {id: $chunk_id})
        SET 
            c.text = $text, 
            c.source = $file_name,
            c.index = $chunk_index
        MERGE (d)-[:HAS_CHUNK]->(c)
        """
        
        with self.driver.session() as session:
            session.run(query, file_name=file_name, chunk_id=chunk_id, text=chunk_text, chunk_index=chunk_index)
        

    def create_entity_and_relate(self, chunk_id: str, entity_name: str, entity_type: str):
        if not self.driver or not entity_name: return
        clean_type = entity_type.capitalize()
        if not clean_type.isalnum(): 
            clean_type = "Entity" 

        query = f"""
        MATCH (c:Chunk {{id: $chunk_id}})
        MERGE (e:{clean_type} {{name: $name}})
        MERGE (c)-[:MENTIONS]->(e)
        """
        with self.driver.session() as session:
            session.run(query, chunk_id=chunk_id, name=entity_name)
       

    def get_chunks_linked_to_entity(self, keyword):
        if not self.driver: return []
        
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (e:Entity)<-[:MENTIONS]-(c:Chunk)
                WHERE toLower(e.name) CONTAINS toLower($keyword)
                RETURN c.text AS text LIMIT 5
                """,
                keyword=keyword
            )
            return list(set([record["text"] for record in result]))

    def get_graph_context(self, file_names: list) -> str:
        if not self.driver or not file_names:
            return ""
        query = """
        MATCH (d:Document)
        WHERE d.name IN $file_names
        RETURN d.name as name, d.created_at as date, count { (d)-[:HAS_CHUNK]->() } as chunk_count
        """
        
        context_parts = []
        with self.driver.session() as session:
            result = session.run(query, file_names=file_names)
            for record in result:
                info = f"Document '{record['name']}' (Indexed on {record['date']}) contains {record['chunk_count']} sections."
                context_parts.append(info)
        
        if context_parts:
            return "GRAPH METADATA:\n" + "\n".join(context_parts)
        return ""

    def get_related_chunks_by_id(self, chunk_ids: list):
        if not self.driver or not chunk_ids:
            return []

        query = """
        MATCH (c:Chunk)
        WHERE c.id IN $chunk_ids
        MATCH (d:Document)-[:HAS_CHUNK]->(c)
        RETURN d.name as source, c.text as text
        """
        with self.driver.session() as session:
            result = session.run(query, chunk_ids=chunk_ids)
            return [record.data() for record in result]
