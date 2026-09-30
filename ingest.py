# =========================
# IMPORTS
# =========================
import os
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from neo4j_db import Neo4jHandler

# =========================
# LOAD ALL FILES
# =========================
documents = []

for file in os.listdir("data"):
    if file.endswith(".txt"):
        loader = TextLoader(f"data/{file}")
        documents.extend(loader.load())

# =========================
# SPLIT
# =========================
splitter = RecursiveCharacterTextSplitter(
    chunk_size=200,
    chunk_overlap=50
)

chunks = splitter.split_documents(documents)
print("Chunks:", len(chunks))

# =========================
# EMBEDDINGS
# =========================
embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# =========================
# FAISS
# =========================
vectorstore = FAISS.from_documents(chunks, embedding)
vectorstore.save_local("faiss_index")

print("Stored in FAISS!")

# =========================
# NEO4J
# =========================
db = Neo4jHandler()

# Example graph data
db.create_attack("Ransomware")
db.create_tool("WannaCry")
db.create_tool("TrickBot")
db.create_vulnerability("SMB")
db.create_vulnerability("EternalBlue")

db.link_attack_tool("Ransomware", "WannaCry")
db.link_attack_tool("Ransomware", "TrickBot")
db.link_attack_vulnerability("Ransomware", "SMB")
db.link_attack_vulnerability("Ransomware", "EternalBlue")

db.close()

print("Stored in Neo4j!")