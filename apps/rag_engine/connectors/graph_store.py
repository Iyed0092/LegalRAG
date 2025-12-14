from neo4j import GraphDatabase
from django.conf import settings

class GraphStoreClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GraphStoreClient, cls).__new__(cls)
            cls._instance.driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
            )
        return cls._instance

    def close(self):
        self.driver.close()

    def create_article_node(self, article_id, title, content_summary):
        query = """
        MERGE (a:Article {id: $id})
        SET a.title = $title, a.summary = $summary
        """
        with self.driver.session() as session:
            session.run(query, id=article_id, title=title, summary=content_summary)

    def create_reference_relationship(self, source_id, target_id):
        query = """
        MATCH (a:Article {id: $source_id})
        MATCH (b:Article {id: $target_id})
        MERGE (a)-[:REFERS_TO]->(b)
        """
        with self.driver.session() as session:
            session.run(query, source_id=source_id, target_id=target_id)

    def get_related_articles(self, article_id):
        query = """
        MATCH (a:Article {id: $id})-[:REFERS_TO]-(related)
        RETURN related.id AS id, related.title AS title
        LIMIT 5
        """
        with self.driver.session() as session:
            result = session.run(query, id=article_id)
            return [record.data() for record in result]