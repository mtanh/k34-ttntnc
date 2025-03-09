from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import os
from typing import List, Tuple
from neo4j import GraphDatabase
from langchain_community.graphs import Neo4jGraph
from langchain_community.vectorstores import Neo4jVector
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores.neo4j_vector import remove_lucene_chars
from langchain_core.prompts.prompt import PromptTemplate
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import (
    RunnableBranch,
    RunnableLambda,
    RunnableParallel,
    RunnablePassthrough,
)
from langchain_core.output_parsers import StrOutputParser

import google.generativeai as genai
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

AURA_INSTANCENAME = os.environ["AURA_INSTANCENAME"]
NEO4J_URI = os.environ["NEO4J_URI"]
NEO4J_USERNAME = os.environ["NEO4J_USERNAME"]
NEO4J_PASSWORD = os.environ["NEO4J_PASSWORD"]
NEO4J_DATABASE = os.environ["NEO4J_DATABASE"]
GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
AUTH = (NEO4J_USERNAME, NEO4J_PASSWORD)

driver = GraphDatabase.driver(NEO4J_URI, auth=AUTH, database=NEO4J_DATABASE)
genai.configure(api_key=GOOGLE_API_KEY)
embedding = GoogleGenerativeAIEmbeddings(
    google_api_key=GOOGLE_API_KEY, model="models/embedding-001"
)
chat = ChatGoogleGenerativeAI(google_api_key=GOOGLE_API_KEY, model="gemini-1.5-flash")

# Initialize Neo4j Graph
kg = Neo4jGraph(
    url=NEO4J_URI,
    username=NEO4J_USERNAME,
    password=NEO4J_PASSWORD,
    database=NEO4J_DATABASE,
)

# Extract entities from text
class Entities(BaseModel):
    """Identifying information about problem-related entities in a customer support ticket."""

    names: List[str] = Field(
        ...,
        description=(
            "A list of problem-related entities extracted from the customer support ticket summary, representing specific issues, "
            "troubles, or technical problems mentioned in the text. These entities include descriptions of malfunctions, errors, "
            "or user-reported difficulties (e.g., 'login issue', 'csv upload error', 'slow performance', 'authentication failure'). "
            "The extraction should focus on identifying key problem terms or phrases relevant to the ticket context, excluding "
            "generic status updates or non-issue terms (e.g., 'reported', 'investigating') unless they form part of a problem "
            "description. For example, in the summary 'John Doe reported a login issue and slow performance with LinkedIn', "
            "the extracted names would be ['login issue', 'slow performance']."
        ),
    )

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are extracting problem-related entities from the text.",
        ),
        (
            "human",
            "Use the given format to extract information from the following "
            "input: {question}",
        ),
    ]
)
entity_chain = prompt | chat.with_structured_output(Entities)

kg.query("CREATE FULLTEXT INDEX entity IF NOT EXISTS FOR (e:__Entity__) ON EACH [e.id]")

def generate_full_text_query(input: str) -> str:
    """
    Generate a full-text search query for a given input string.

    This function constructs a query string suitable for a full-text search.
    It processes the input string by splitting it into words and appending a
    similarity threshold (~2 changed characters) to each word, then combines
    them using the AND operator. Useful for mapping entities from user questions
    to database values, and allows for some misspellings.
    """
    full_text_query = ""
    words = [el for el in remove_lucene_chars(input).split() if el]
    for word in words[:-1]:
        full_text_query += f" {word}~2 AND"
    full_text_query += f" {words[-1]}~2"
    return full_text_query.strip()


def structured_retriever(question: str) -> str:
    """
    Collects the neighborhood of entities mentioned
    in the question
    """
    result = ""
    entities = entity_chain.invoke({"question": question})
    for entity in entities.names:
        print(f" Getting Entity: {entity}")
        response = kg.query(
            """CALL db.index.fulltext.queryNodes('entity', $query, {limit:2})
            YIELD node,score
            CALL {
              WITH node
              MATCH (node)-[r:!HAS_SUMMARY]->(neighbor)
              RETURN node.id + ' - ' + type(r) + ' -> ' + neighbor.id AS output
              UNION ALL
              WITH node
              MATCH (node)<-[r:!HAS_SUMMARY]-(neighbor)
              RETURN neighbor.id + ' - ' + type(r) + ' -> ' +  node.id AS output
            }
            RETURN output LIMIT 50
            """,
            {"query": generate_full_text_query(entity)},
        )
        result += "\n".join([el["output"] for el in response])
    return result


summary_vector_index = Neo4jVector.from_existing_graph(
    GoogleGenerativeAIEmbeddings(
        google_api_key=GOOGLE_API_KEY, model="models/embedding-001"
    ),
    search_type="hybrid",
    node_label="Summary",
    text_node_properties=["summary"],
    embedding_node_property="embedding",
)

def retriever(question: str):
    print(f"Search query: {question}")
    structured_data = structured_retriever(question)
    unstructured_data = [
        el.page_content for el in summary_vector_index.similarity_search(question)
    ]
    final_data = f"""Structured data:
        {structured_data}
        Unstructured data:
        {"#Summary ".join(unstructured_data)}
        """
    print(f"\nFinal Data::: ==>{final_data}")
    return final_data


_template = """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question,
in its original language.
Chat History:
{chat_history}
Follow Up Input: {question}
Standalone question:"""  # noqa: E501
CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(_template)

def _format_chat_history(chat_history: List[Tuple[str, str]]) -> List:
    buffer = []
    for human, ai in chat_history:
        buffer.append(HumanMessage(content=human))
        buffer.append(AIMessage(content=ai))
    return buffer


_search_query = RunnableBranch(
    (
        RunnableLambda(lambda x: bool(x.get("chat_history"))).with_config(
            run_name="HasChatHistoryCheck"
        ),
        RunnablePassthrough.assign(
            chat_history=lambda x: _format_chat_history(x["chat_history"])
        )
        | CONDENSE_QUESTION_PROMPT
        | chat
        | StrOutputParser(),
    ),
    RunnableLambda(lambda x: x["question"]),
)

template = """Answer the question based only on the following context:
{context}

Question: {question}
Use natural language and be concise.
Answer:"""
prompt = ChatPromptTemplate.from_template(template)

chain = (
    RunnableParallel(
        {
            "context": _search_query | retriever,
            "question": RunnablePassthrough(),
        }
    )
    | prompt
    | chat
    | StrOutputParser()
)

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

    response = chain.invoke({"question": question})
    return jsonify({"answer": response})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

# Run: `python app.py`
