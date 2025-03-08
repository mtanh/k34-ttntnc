"""Clean up the Knowledge Graph by removing all nodes and relationships."""

from dotenv import load_dotenv
import os
from neo4j import GraphDatabase

load_dotenv()

AURA_INSTANCENAME = os.environ["AURA_INSTANCENAME"]
NEO4J_URI = os.environ["NEO4J_URI"]
NEO4J_USERNAME = os.environ["NEO4J_USERNAME"]
NEO4J_PASSWORD = os.environ["NEO4J_PASSWORD"]
NEO4J_DATABASE = os.environ["NEO4J_DATABASE"]
AUTH = (NEO4J_USERNAME, NEO4J_PASSWORD)

driver = GraphDatabase.driver(NEO4J_URI, auth=AUTH, database=NEO4J_DATABASE)


# Function to delete everything
def clean_neo4j(session):
    # Remove all relationships
    session.run("MATCH ()-[r]->() DELETE r")
    print("Deleted all relationships.")

    # Remove all nodes
    session.run("MATCH (n) DELETE n")
    print("Deleted all nodes.")

    # Drop all constraints
    constraints = session.run("SHOW CONSTRAINTS")
    for record in constraints:
        session.run(f"DROP CONSTRAINT {record['name']}")
    print("Dropped all constraints.")

    # Drop all indexes
    indexes = session.run("SHOW INDEXES")
    for record in indexes:
        session.run(f"DROP INDEX {record['name']}")
    print("Dropped all indexes.")

# Run cleanup
with driver.session() as session:
    clean_neo4j(session)

# Close connection
driver.close()
print("Neo4j Aura is fully cleaned.")
