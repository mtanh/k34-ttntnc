from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import os
import json
import re
import logging
from typing import List, Dict
from neo4j import GraphDatabase
from langchain_neo4j import Neo4jGraph
from langchain_community.vectorstores import Neo4jVector
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from pydantic import BaseModel, Field

# Configure logging to suppress Neo4j warnings
logging.getLogger("neo4j").setLevel(logging.ERROR)

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
NEO4J_URI = os.environ["NEO4J_URI"]
NEO4J_USERNAME = os.environ["NEO4J_USERNAME"]
NEO4J_PASSWORD = os.environ["NEO4J_PASSWORD"]
NEO4J_DATABASE = os.environ["NEO4J_DATABASE"]

# Initialize Neo4j driver and graph
driver = GraphDatabase.driver(
    NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD), database=NEO4J_DATABASE
)
kg = Neo4jGraph(
    url=NEO4J_URI,
    username=NEO4J_USERNAME,
    password=NEO4J_PASSWORD,
    database=NEO4J_DATABASE,
)

# Initialize Google Gemini API
embeddings = GoogleGenerativeAIEmbeddings(
    google_api_key=GOOGLE_API_KEY, model="models/embedding-001"
)
llm = ChatGoogleGenerativeAI(google_api_key=GOOGLE_API_KEY, model="gemini-1.5-flash")


# 3.2.1 Query Entity Identification and Intent Detection
class IssueEntities(BaseModel):
    """Model for extracting problem-related entities and intents from customer support tickets."""

    entities: Dict[str, str] = Field(
        ...,
        description=(
            "A dictionary of problem-related entities extracted from customer support tickets, where keys are sections "
            "from the ticket template (e.g., 'issue summary', 'issue description', 'step to reproduce') and values are "
            "specific issues, troubles, or technical difficulties (e.g., 'csv upload error', 'login issue', 'slow "
            "response time'). The extraction should focus on key problem terms or phrases relevant to the ticket "
            "context, excluding generic terms (e.g., 'reported', 'investigating', 'user'), status updates, or "
            "procedural notes unless part of a problem description. For example, in 'User reported a login issue and "
            "slow response time while accessing the app', the entities would be {'issue summary': 'login issue', "
            "'issue description': 'slow response time while accessing the app'}."
        ),
    )
    intents: List[str] = Field(
        ...,
        description=(
            "A list of query intents representing the user's goal (e.g., 'fix solution', 'reproduce issue'), derived "
            "from the entities and context of the ticket. Intents should reflect actionable outcomes relevant to the "
            "query, such as providing a solution or steps to reproduce."
        ),
    )


# Fallback parsing for plain text responses
def fallback_parse_text(text: str, query: str) -> Dict:
    """Extract entities and intents from plain text if JSON parsing fails."""
    entities = {}
    intents = []

    # Look for common issue-related phrases
    if "error" in query.lower():
        entities["issue summary"] = " ".join(
            [word for word in query.split() if "error" in word.lower()]
        )
    elif "issue" in query.lower():
        entities["issue summary"] = " ".join(
            [word for word in query.split() if "issue" in word.lower()]
        )

    # Look for additional descriptions
    if "priority" in query.lower() or "due to" in query.lower():
        entities["issue description"] = query

    # Determine intents based on keywords
    if "how to reproduce" in query.lower():
        intents.append("reproduce issue")
    else:
        intents.append("fix solution")

    # If no entities were extracted, use a default
    if not entities:
        entities["issue summary"] = query

    return {"entities": entities, "intents": intents}


# Custom parsing function to handle JSON string outputs
def parse_structured_output(response: str, query: str) -> Dict:
    """Parse the structured output from Gemini API, handling both dict and JSON string cases."""
    if isinstance(response, dict):
        return response
    elif isinstance(response, str):
        # Try to extract JSON from the response using regex
        json_match = re.search(r"\{.*\}", response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            try:
                return json.loads(json_str)  # Parse JSON string into a dictionary
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON string: {e}, Raw response: {response}")
        print(
            f"Could not parse response as JSON, falling back to text parsing: {response}"
        )
        return fallback_parse_text(response, query)
    else:
        print(f"Unexpected response type: {type(response)}, Response: {response}")
        return fallback_parse_text(str(response), query)


# Create the entity chain with custom parsing
entity_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert in analyzing customer support tickets, tasked with extracting problem-related entities "
            "and intents. Extract entities as a dictionary mapping ticket sections (e.g., 'issue summary', 'issue "
            "description', 'step to reproduce') to specific issues, troubles, or technical difficulties. Identify "
            "intents as a list of actionable goals (e.g., 'fix solution', 'reproduce issue'). Exclude generic terms "
            "(e.g., 'reported', 'investigating', 'user'), status updates, or procedural notes unless part of a problem "
            "description. Return the entities and intents based on the ticket context as a valid JSON object in the "
            "format: {{'entities': {{'issue summary': '...', 'issue description': '...'}}, 'intents': ['...']}}. "
            "Ensure the output is strictly a JSON object with proper syntax (e.g., use double quotes for keys and values).",
        ),
        (
            "human",
            "Extract problem-related entities and intents from the following customer support ticket: {question}",
        ),
    ]
)

# Use RunnableParallel to carry the input query alongside the LLM output
entity_chain = (
    RunnableParallel(response=entity_prompt | llm, query=RunnablePassthrough())
    | (lambda x: parse_structured_output(x["response"].content, x["query"]["question"]))
    | (lambda x: IssueEntities(**x))
)


# 3.2.2 Embedding-based Retrieval of Sub-graphs
def generate_full_text_query(input: str) -> str:
    """Generate a full-text search query with fuzzy matching."""
    words = [
        el for el in input.split() if el
    ]  # Simplified, assuming no special chars for now
    full_text_query = " ".join(f"{word}~2" for word in words)
    return full_text_query.strip()


# Initialize vector indexes based on the second script
summary_vector_index = Neo4jVector.from_existing_graph(
    embeddings,
    search_type="hybrid",
    node_label="Summary",
    text_node_properties=["summary"],
    embedding_node_property="embedding",
)

description_vector_index = Neo4jVector.from_existing_graph(
    embeddings,
    search_type="hybrid",
    node_label="IssueDescription",
    text_node_properties=["description"],
    embedding_node_property="embedding",
)

steps_vector_index = Neo4jVector.from_existing_graph(
    embeddings,
    search_type="hybrid",
    node_label="StepReproduce",
    text_node_properties=["step"],
    embedding_node_property="embedding",
)


def get_top_ticket_id(entities: Dict[str, str]) -> str:
    """Retrieve the top ticket ID using embedding-based retrieval across multiple sections."""
    if not entities:
        return "ENT-23000"  # Default fallback to the first ticket

    # Aggregate scores from multiple entity sections
    max_score = -1
    best_ticket_id = "ENT-23000"

    for section, value in entities.items():
        vector_index = {
            "issue summary": summary_vector_index,
            "issue description": description_vector_index,
            "step to reproduce": steps_vector_index,
        }.get(
            section, summary_vector_index
        )  # Default to summary if section not matched

        results = vector_index.similarity_search_with_score(value, k=1)
        if results:
            doc, score = results[0]
            metadata = doc.metadata
            summary_id = metadata.get("id", doc.page_content)
            cypher_query = """
            MATCH (s)-[:HAS_SUMMARY|HAS_ISSUE_DESCRIPTION|HAS_STEPS_TO_REPRODUCE]->(n)
            WHERE s.id = $summary_id AND (n:Summary OR n:IssueDescription OR n:StepReproduce)
            MATCH (t:Ticket)-[:HAS_SUMMARY|HAS_ISSUE_DESCRIPTION|HAS_STEPS_TO_REPRODUCE]->(n)
            RETURN t.code AS ticket_id
            """
            result = kg.query(cypher_query, {"summary_id": summary_id})
            if result and score > max_score:
                max_score = score
                best_ticket_id = result[0]["ticket_id"]

    # Fallback to full-text search if no vector match
    if max_score == -1:
        full_text_query = generate_full_text_query(list(entities.values())[0])
        cypher_query = """
        CALL db.index.fulltext.queryNodes('summary_fulltext', $query, {limit: 1})
        YIELD node
        MATCH (t:Ticket)-[:HAS_SUMMARY]->(node)
        RETURN t.code AS ticket_id
        """
        result = kg.query(cypher_query, {"query": full_text_query})
        return result[0]["ticket_id"] if result else "ENT-23000"

    return best_ticket_id


def rephrase_query(original_query: str, ticket_id: str) -> str:
    """Rephrase the query to include the ticket ID using LLM."""
    rephrase_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are reformulating customer support queries to include a ticket ID for subgraph extraction.",
            ),
            (
                "human",
                f"Original query: {original_query}\nRetrieved ticket ID: {ticket_id}\nRephrase the query to include the ticket ID:",
            ),
        ]
    )
    rephrase_chain = rephrase_prompt | llm | StrOutputParser()
    return rephrase_chain.invoke({})


def generate_cypher_query(rephrased_query: str, ticket_id: str) -> str:
    """Generate a Cypher query based on the rephrased query."""
    if "how to reproduce" in rephrased_query.lower():
        return """
        MATCH (t:Ticket {code: $ticket_id})
        OPTIONAL MATCH (t)-[:HAS_ISSUE_DESCRIPTION]->(d:IssueDescription)
        OPTIONAL MATCH (t)-[:HAS_STEPS_TO_REPRODUCE]->(s:StepReproduce)
        RETURN d.description AS description, s.step AS steps_to_reproduce
        """
    return """
    MATCH (t:Ticket {code: $ticket_id})
    RETURN t.code AS ticket_id
    LIMIT 1
    """


def retrieve_subgraph(ticket_id: str) -> Dict:
    """Retrieve subgraph data using Cypher query."""
    cypher_query = generate_cypher_query(f"how to reproduce {ticket_id}", ticket_id)
    result = kg.query(cypher_query, {"ticket_id": ticket_id})
    if result:
        return {
            "description": result[0].get("description", "No description found"),
            "steps_to_reproduce": result[0].get("steps_to_reproduce", "No steps found"),
        }
    return {"error": "No subgraph data found for ticket " + ticket_id}


# 3.2.3 Answer Generation
def generate_answer(query: str, context: Dict) -> str:
    """Generate a natural language answer using LLM."""
    answer_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a customer support expert generating answers based on retrieved ticket data.",
            ),
            (
                "human",
                f"Query: {query}\nContext: Description: {context.get('description', '')}, Steps to Reproduce: {context.get('steps_to_reproduce', '')}\nProvide a concise answer:",
            ),
        ]
    )
    answer_chain = answer_prompt | llm | StrOutputParser()
    return answer_chain.invoke({})


# Full Implementation
def process_query(query: str) -> Dict:
    """Process the full retrieval and question answering workflow."""
    # 3.2.1: Query Entity Identification and Intent Detection
    try:
        entities_intents = entity_chain.invoke({"question": query})
        print(f"*** Extracted Entities: {entities_intents.entities}")
        print(f"*** Extracted Intents: {entities_intents.intents}")
    except Exception as e:
        print(f"Error extracting entities and intents: {e}")
        entities_intents = IssueEntities(
            entities={"issue summary": query}, intents=["reproduce issue"]
        )  # Fallback

    # 3.2.2: Embedding-based Retrieval of Sub-graphs
    ticket_id = get_top_ticket_id(entities_intents.entities)
    print(f"*** Retrieved Ticket ID: {ticket_id}")

    rephrased_query = rephrase_query(query, ticket_id)
    print(f"*** Rephrased Query: {rephrased_query}")

    subgraph_data = retrieve_subgraph(ticket_id)
    print(f"*** Subgraph Data: {subgraph_data}")

    # 3.2.3: Answer Generation
    answer = generate_answer(query, subgraph_data)
    print(f"*** Generated Answer: {answer}")

    # Convert Pydantic model to dictionary for JSON serialization
    response = {
        "entities": entities_intents.model_dump()["entities"],
        "intents": entities_intents.model_dump()["intents"],
        "ticket_id": ticket_id,
        "subgraph_data": subgraph_data,
        "answer": answer,
    }
    return response


# Flask application
app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    question = data.get("question")
    if not question:
        return jsonify({"error": "No question provided"}), 400

    # response = chain.invoke({"question": question})
    response = process_query(question)
    return jsonify(response)  # jsonify will handle the dictionary


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

# Run: `python app.py`
