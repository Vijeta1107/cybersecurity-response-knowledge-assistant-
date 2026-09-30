from neo4j_db import Neo4jHandler

db = Neo4jHandler()

db.create_tool("WannaCry")
db.create_vulnerability("SMB Exploit")

db.link_attack_tool("Ransomware", "WannaCry")
db.link_attack_vulnerability("Ransomware", "SMB Exploit")

db.close()