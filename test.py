from neo4j_db import Neo4jHandler

db = Neo4jHandler()

db.create_attack("Ransomware")
print("Inserted!")

db.close()