from dotenv import load_dotenv
import os
from neo4j import GraphDatabase
from langchain_community.graphs import Neo4jGraph
from langchain_community.vectorstores import Neo4jVector
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai

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

# Initialize Neo4j Graph
kg = Neo4jGraph(
    url=NEO4J_URI,
    username=NEO4J_USERNAME,
    password=NEO4J_PASSWORD,
    database=NEO4J_DATABASE,
)


def get_gemini_embedding_768(text):
    """Fetches a 768D embedding using Google Gemini API"""
    response = genai.embed_content(
        model="models/embedding-001",  # 768D embedding model
        content=text,
        task_type="retrieval_document",
    )

    if isinstance(response, dict) and "embedding" in response:
        return response["embedding"]  # Returns a 768D list

    print("Error:", response)
    return None


def store_issue_summary_embeddings():
    try:
        vector_index = Neo4jVector.from_existing_graph(
            GoogleGenerativeAIEmbeddings(
                google_api_key=GOOGLE_API_KEY, model="models/embedding-001"
            ),  # use embedding-001
            search_type="hybrid",
            node_label="Summary",
            index_name="issue_summary_vector_index",
            text_node_properties=["summary"],
            embedding_node_property="embedding",
        )
        # print("Vector index created successfully.")
    except Exception as e:
        print(f"Error creating vector index: {e}")


def store_issue_description_embeddings():
    try:
        vector_index = Neo4jVector.from_existing_graph(
            GoogleGenerativeAIEmbeddings(
                google_api_key=GOOGLE_API_KEY, model="models/embedding-001"
            ),  # use embedding-001
            search_type="hybrid",
            node_label="IssueDescription",
            index_name="issue_description_vector_index",
            text_node_properties=["description"],
            embedding_node_property="embedding",
        )
        # print("Vector index created successfully.")
    except Exception as e:
        print(f"Error creating vector index: {e}")


def store_steps_reproduce_embeddings():
    try:
        vector_index = Neo4jVector.from_existing_graph(
            GoogleGenerativeAIEmbeddings(
                google_api_key=GOOGLE_API_KEY, model="models/embedding-001"
            ),  # use embedding-001
            search_type="hybrid",
            node_label="StepReproduce",
            index_name="step_reproduce_vector_index",
            text_node_properties=["step"],
            embedding_node_property="embedding",
        )
        # print("Vector index created successfully.")
    except Exception as e:
        print(f"Error creating vector index: {e}")


def create_vector_index(node_label, index_name, text_property):
    """Create a vector index for Neo4j."""
    try:
        vector_index = Neo4jVector.from_existing_graph(
            GoogleGenerativeAIEmbeddings(
                google_api_key=GOOGLE_API_KEY, model="models/embedding-001"
            ),
            search_type="hybrid",  # Requires full-text + vector index
            node_label=node_label,
            index_name=index_name,
            text_node_properties=[text_property],
            embedding_node_property="embedding",
        )
        print(
            f"Vector index '{index_name}' for label '{node_label}' created successfully."
        )
    except Exception as e:
        print(
            f"Error creating vector index '{index_name}' for label '{node_label}': {e}"
        )


def create_issue_summary_vector_index():
    kg.query(
        """
        CREATE FULLTEXT INDEX summary_fulltext IF NOT EXISTS
        FOR (s:Summary) ON EACH [s.summary];
        """
    )
    kg.query(
        """
        CREATE VECTOR INDEX summary_embeddings IF NOT EXISTS
        FOR (s:Summary) ON (s.embedding)
        OPTIONS {
        indexConfig: {
            `vector.dimensions`: 768,
            `vector.similarity_function`: 'cosine'
        }
        }
        """
    )
    create_vector_index("Summary", "summary_embeddings", "summary")


def create_issue_description_vector_index():
    kg.query(
        """
        CREATE FULLTEXT INDEX issue_description_fulltext IF NOT EXISTS
        FOR (id:IssueDescription) ON EACH [id.description];
        """
    )
    kg.query(
        """
        CREATE VECTOR INDEX issue_description_embeddings IF NOT EXISTS
        FOR (id:IssueDescription) ON (id.embedding)
        OPTIONS {
            indexConfig: {
                `vector.dimensions`: 768,
                `vector.similarity_function`: 'cosine'
            }
        }
        """
    )
    create_vector_index(
        "IssueDescription", "issue_description_embeddings", "description"
    )


def create_step_reproduce_vector_index():
    kg.query(
        """
        CREATE FULLTEXT INDEX step_reproduce_fulltext IF NOT EXISTS
        FOR (sr:StepReproduce) ON EACH [sr.step];
        """
    )
    kg.query(
        """
        CREATE VECTOR INDEX step_reproduce_embeddings IF NOT EXISTS
        FOR (sr:StepReproduce) ON (sr.embedding)
        OPTIONS {
            indexConfig: {
                `vector.dimensions`: 768,
                `vector.similarity_function`: 'cosine'
            }
        }
        """
    )
    create_vector_index("StepReproduce", "step_reproduce_embeddings", "step")


def _get_all_indexes():
    """Retrieve all indexes from Neo4j."""
    indexes = kg.query("SHOW INDEXES")
    print("\nAll Indexes in Neo4j:")
    for index in indexes:
        print(index)
    return indexes


def test_vector_index(index_name, node_label, text_property, query_text):
    """Test a vector index by performing a similarity search and printing scores."""
    try:
        print(f"\nTesting Vector Index: {index_name} on {node_label}")

        vector_index = Neo4jVector.from_existing_graph(
            GoogleGenerativeAIEmbeddings(
                google_api_key=GOOGLE_API_KEY, model="models/embedding-001"
            ),
            search_type="hybrid",
            node_label=node_label,
            index_name=index_name,
            text_node_properties=[text_property],
            embedding_node_property="embedding",
        )

        # Perform a similarity search
        results = vector_index.similarity_search_with_score(query_text, k=3)

        print("\nSearch Results with Similarity Scores:")
        for result, score in results:
            print(f"Node: {result.page_content} | Score: {score}")

    except Exception as e:
        print(f"Error Testing Vector Index '{index_name}': {e}")


if __name__ == "__main__":

    # create_issue_summary_vector_index()
    # create_issue_description_vector_index()
    # create_step_reproduce_vector_index()

    # _get_all_indexes()
    # test_vector_index(
    #     "step_reproduce_embeddings", "StepReproduce", "step", "authentication"
    # )

    pass
