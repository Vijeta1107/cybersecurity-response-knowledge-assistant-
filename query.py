# query.py
# =========================
# IMPORTS
# =========================
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from neo4j_db import Neo4jHandler
from dotenv import load_dotenv
import os
import json

# =========================
# SETUP
# =========================
load_dotenv()

embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

vectorstore = FAISS.load_local(
    "faiss_index",
    embedding,
    allow_dangerous_deserialization=True
)

db = Neo4jHandler()

llm = ChatGroq(
    model_name="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY")
)


# =========================
# INPUT SECURITY GUARDRAIL
# (Architecture: Step 2 - Input Security / Security_Gate)
# Checks for harmful, malicious, or prompt injection queries
# before routing to the LLM pipeline.
# =========================
MALICIOUS_KEYWORDS = [
    # Offensive hacking terms
    "how to hack", "how to exploit", "how to crack", "how to bypass",
    "write malware", "create malware", "create ransomware", "build ransomware",
    "write a virus", "create a virus", "write a keylogger", "create a keylogger",
    "write exploit", "create exploit", "sql injection attack", "xss attack payload",
    "ddos attack script", "dos attack", "brute force script", "password cracker",
    "reverse shell", "bind shell", "remote access trojan", "rat payload",
    "metasploit payload", "meterpreter", "phishing page creator",
    "credential harvester", "stealing credentials", "bypass firewall",
    "bypass antivirus", "evade detection", "rootkit install",
    # Prompt injection patterns
    "ignore previous instructions", "disregard system prompt",
    "you are now", "pretend you are", "act as an unrestricted",
    "jailbreak", "dan mode", "developer mode",
]

def is_malicious_query(query: str) -> bool:
    """
    Input Guardrail (Security Gate - Architecture Node F/G).
    Returns True if the query matches known harmful/injection patterns.
    """
    q = query.lower()
    for keyword in MALICIOUS_KEYWORDS:
        if keyword in q:
            return True
    return False


def llm_safety_check(query: str) -> bool:
    """
    LLM-based secondary safety check for subtle harmful queries.
    Returns True if query is safe, False if harmful.
    """
    prompt = f"""
    You are a cybersecurity assistant safety classifier.
    Classify this user query as SAFE or HARMFUL.

    HARMFUL = asking how to attack, exploit, hack, create malware, steal data, bypass security, or any offensive action.
    SAFE = asking about concepts, definitions, investigation, defense, prevention, or general cybersecurity knowledge.

    Return ONLY one word: SAFE or HARMFUL.

    Query: {query}
    """
    result = llm.invoke(prompt).content.strip().upper()
    return "HARMFUL" not in result


# =========================
# CLASSIFIER
# =========================
def classify_query(query):
    prompt = f"""
    Classify this query into ONE category:

    - DEFINITION (what is, explain)
    - RELATIONSHIP (tools, vulnerabilities, graph)
    - INCIDENT (attack detected, investigation)
    - PREVENTION (how to prevent, how to secure)

    Return ONLY one word.

    Query: {query}
    """
    return llm.invoke(prompt).content.strip().upper()


# =========================
# ROUTER
# =========================
def route_query(query):
    qtype = classify_query(query)

    if "DEFINITION" in qtype:
        return "VECTOR", "DEFINITION"
    elif "RELATIONSHIP" in qtype:
        return "GRAPH", "RELATIONSHIP"
    elif "PREVENTION" in qtype:
        return "VECTOR", "PREVENTION"
    else:
        return "BOTH", "INCIDENT"


# =========================
# VECTOR RETRIEVAL
# =========================
def retrieve_docs(query):
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    docs = retriever.invoke(query)
    return "\n".join([d.page_content for d in docs])


# =========================
# GRAPH RETRIEVAL
# =========================
def retrieve_graph():
    try:
        cypher = """
        MATCH (a:Attack)-[r]->(b)
        RETURN a, r, b LIMIT 5
        """
        return str(db.run_query(cypher))
    except:
        return ""


# =========================
# SAFE JSON PARSER
# =========================
def parse_response(response):
    try:
        # Strip markdown code fences if present
        clean = response.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        data = json.loads(clean.strip())
        return {
            "summary": data.get("summary", ""),
            "causes": data.get("causes", []),
            "investigation": data.get("investigation", []),
            "mitigation": data.get("mitigation", [])
        }
    except:
        return {
            "summary": response,
            "causes": [],
            "investigation": [],
            "mitigation": []
        }


# =========================
# MAIN FUNCTION
# =========================
def ask(query):
    try:
        # ------------------------------------------
        # STEP 1: INPUT SECURITY GUARDRAIL
        # Architecture: Node F → G (Block/Alert)
        # ------------------------------------------

        # Fast keyword check first
        if is_malicious_query(query):
            return {
                "summary": "⚠️ This query has been blocked by the Input Security Guardrail. It appears to request offensive or harmful cybersecurity actions.",
                "causes": [],
                "investigation": [],
                "mitigation": [
                    "I can help you with cybersecurity defense, threat analysis, and prevention.",
                    "Ask me about incident response, vulnerability management, or security best practices."
                ],
                "blocked": True
            }

        # LLM-based safety check for subtle harmful queries
        if not llm_safety_check(query):
            return {
                "summary": "⚠️ Query blocked by AI safety check. This request appears to involve offensive cybersecurity actions that I cannot assist with.",
                "causes": [],
                "investigation": [],
                "mitigation": [
                    "I specialize in cybersecurity defense and threat intelligence.",
                    "Try asking about how to defend against attacks, investigate incidents, or secure your systems."
                ],
                "blocked": True
            }

        # ------------------------------------------
        # STEP 2: ROUTE + RETRIEVE (Agentic Loop)
        # ------------------------------------------
        route, qtype = route_query(query)

        vector_context = ""
        graph_context = ""

        if route in ["VECTOR", "BOTH"]:
            vector_context = retrieve_docs(query)

        if route in ["GRAPH", "BOTH"]:
            graph_context = retrieve_graph()

        full_context = f"""
        Vector:
        {vector_context}

        Graph:
        {graph_context}
        """

        # ------------------------------------------
        # STEP 3: TYPE-BASED PROMPTS
        # ------------------------------------------
        if qtype == "PREVENTION":
            prompt = f"""
            You are a cybersecurity expert assistant.

            Return ONLY valid JSON (no markdown, no extra text):

            {{
              "summary": "short explanation about preventing this threat",
              "causes": ["general risk 1", "general risk 2"],
              "investigation": [],
              "mitigation": ["prevention step 1", "prevention step 2", "prevention step 3"]
            }}

            Rules:
            - Focus on general cybersecurity practices
            - DO NOT include investigation steps
            - Keep everything concise (1 line per point)

            Context:
            {full_context}

            Question: {query}
            """

        elif qtype == "DEFINITION":
            prompt = f"""
            You are a cybersecurity expert assistant.

            Return ONLY valid JSON (no markdown, no extra text):

            {{
              "summary": "clear 2-3 line explanation of the concept",
              "causes": [],
              "investigation": [],
              "mitigation": []
            }}

            Question: {query}
            """

        elif qtype == "RELATIONSHIP":
            prompt = f"""
            You are a cybersecurity expert assistant.

            Return ONLY valid JSON (no markdown, no extra text):

            {{
              "summary": "short explanation of the relationship",
              "causes": [],
              "investigation": ["relationship detail 1", "relationship detail 2"],
              "mitigation": []
            }}

            Use graph context below.

            Context:
            {full_context}

            Question: {query}
            """

        else:  # INCIDENT
            prompt = f"""
            You are a cybersecurity expert assistant.

            Return ONLY valid JSON (no markdown, no extra text):

            {{
              "summary": "brief 2-3 line explanation of the incident",
              "causes": ["cause 1", "cause 2", "cause 3"],
              "investigation": ["investigation step 1", "investigation step 2", "investigation step 3"],
              "mitigation": ["mitigation action 1", "mitigation action 2", "mitigation action 3"]
            }}

            Rules:
            - Keep each point to 1 line
            - Do not repeat similar ideas
            - Use simple professional language

            Context:
            {full_context}

            Question: {query}
            """

        # ------------------------------------------
        # STEP 4: LLM CALL
        # ------------------------------------------
        response = llm.invoke(prompt).content
        result = parse_response(response)
        result["blocked"] = False
        return result

    except Exception as e:
        return {
            "summary": f"Error: {e}",
            "causes": [],
            "investigation": [],
            "mitigation": [],
            "blocked": False
        }


# =========================
# CLI TEST
# =========================
if __name__ == "__main__":
    print("\n🚀 System Ready\n")
    while True:
        q = input("Ask: ")
        if q.lower() == "exit":
            break
        print("\n💡", ask(q), "\n")