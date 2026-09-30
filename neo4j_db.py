# neo4j_db.py

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Neo4jHandler:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI")
        self.username = os.getenv("NEO4J_USERNAME")
        self.password = os.getenv("NEO4J_PASSWORD")

        if not all([self.uri, self.username, self.password]):
            raise ValueError("Neo4j credentials not found in .env")

        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(self.username, self.password)
        )

    def close(self):
        self.driver.close()

    # ----------------------------
    # BASIC QUERY RUNNER
    # ----------------------------
    def run_query(self, query, parameters=None):
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

    # ----------------------------
    # CREATE NODES
    # ----------------------------
    def create_attack(self, name, description=""):
        query = """
        MERGE (a:Attack {name: $name})
        SET a.description = $description
        """
        self.run_query(query, {"name": name, "description": description})

    def create_tool(self, name):
        query = """
        MERGE (t:Tool {name: $name})
        """
        self.run_query(query, {"name": name})

    def create_vulnerability(self, name):
        query = """
        MERGE (v:Vulnerability {name: $name})
        """
        self.run_query(query, {"name": name})

    # ----------------------------
    # CREATE RELATIONSHIPS
    # ----------------------------
    def link_attack_tool(self, attack, tool):
        query = """
        MATCH (a:Attack {name: $attack})
        MATCH (t:Tool {name: $tool})
        MERGE (a)-[:USES]->(t)
        """
        self.run_query(query, {"attack": attack, "tool": tool})

    def link_attack_vulnerability(self, attack, vulnerability):
        query = """
        MATCH (a:Attack {name: $attack})
        MATCH (v:Vulnerability {name: $vulnerability})
        MERGE (a)-[:EXPLOITS]->(v)
        """
        self.run_query(query, {
            "attack": attack,
            "vulnerability": vulnerability
        })

    # ----------------------------
    # SEARCH / RETRIEVE
    # ----------------------------
    def get_attack_details(self, name):
        query = """
        MATCH (a:Attack {name: $name})
        OPTIONAL MATCH (a)-[:USES]->(t:Tool)
        OPTIONAL MATCH (a)-[:EXPLOITS]->(v:Vulnerability)
        RETURN a.name AS attack,
               collect(DISTINCT t.name) AS tools,
               collect(DISTINCT v.name) AS vulnerabilities
        """
        return self.run_query(query, {"name": name})

    # ----------------------------
    # CLEAR DATABASE (optional)
    # ----------------------------
    def clear_db(self):
        query = "MATCH (n) DETACH DELETE n"
        self.run_query(query)