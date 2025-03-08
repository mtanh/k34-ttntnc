from dotenv import load_dotenv
import os
import csv
from neo4j import GraphDatabase

load_dotenv()

AURA_INSTANCENAME = os.environ["AURA_INSTANCENAME"]
NEO4J_URI = os.environ["NEO4J_URI"]
NEO4J_USERNAME = os.environ["NEO4J_USERNAME"]
NEO4J_PASSWORD = os.environ["NEO4J_PASSWORD"]
NEO4J_DATABASE = os.environ["NEO4J_DATABASE"]
AUTH = (NEO4J_USERNAME, NEO4J_PASSWORD)

driver = GraphDatabase.driver(NEO4J_URI, auth=AUTH, database=NEO4J_DATABASE)

# Function to connect and run a Cypher query
def execute_query(driver, cypher_query, parameters=None):
    try:
        with driver.session(database=NEO4J_DATABASE) as session:
            session.run(cypher_query, parameters)
    except Exception as e:
        print(f"Error: {e}")

# Function to create ticket nodes
def create_ticket_node(driver, code, title):
    print("Creating ticket node")
    create_provider_query = """
    MERGE (t:Ticket {code: $code, title: $title})
    """
    parameters = {"code": code, "title": title}
    execute_query(driver, create_provider_query, parameters)

# Function to create summary nodes
def create_summary_node(driver, summary):
    print("Creating summary node")
    create_provider_query = """
    MERGE (s:Summary {summary: $summary})
    """
    parameters = {"summary": summary}
    execute_query(driver, create_provider_query, parameters)


# Function to create description nodes and establish relationships
def create_description_node(driver, issue_description_text, step_reproduce_text):
    print("Creating description node")

    # Create IssueDescription node
    print("  Creating issue description node")
    query_issue_desc = """
    MERGE (id:IssueDescription {description: $description}) RETURN id
    """
    execute_query(driver, query_issue_desc, {"description": issue_description_text})

    # Create StepReproduce node
    print("  Creating step reproduce node")
    query_step_reproduce = """
    MERGE (sr:StepReproduce {step: $step}) RETURN sr
    """
    execute_query(driver, query_step_reproduce, {"step": step_reproduce_text})

    # Create Description node
    print("  Creating Description node")
    query_description = "MERGE (d:Description) RETURN d"
    execute_query(driver, query_description)

    # Create Relationships
    print("  Creating relationships")
    query_relationships = """
    MATCH (d:Description), (id:IssueDescription {description: $description})
    MERGE (d)-[:HAS_ISSUE_DESCRIPTION]->(id)
    WITH d
    MATCH (d), (sr:StepReproduce {step: $step})
    MERGE (d)-[:HAS_STEPS_TO_REPRODUCE]->(sr)
    """
    parameters = {"description": issue_description_text, "step": step_reproduce_text}
    execute_query(driver, query_relationships, parameters)


# Function to create fields nodes and establish relationships
def create_fields_node(driver, priority_text, root_cause_text, impact_area_text):
    print("Creating fields node")

    # Create Priority node
    print("  Creating priority node")
    query_issue_desc = """
    MERGE (p:Priority {priority: $priority}) RETURN p
    """
    execute_query(driver, query_issue_desc, {"priority": priority_text})

    # Create RootCause node
    print("  Creating root cause node")
    query_step_reproduce = """
    MERGE (rc:RootCause {root_cause: $root_cause}) RETURN rc
    """
    execute_query(driver, query_step_reproduce, {"root_cause": root_cause_text})

    # Create ImpactArea node
    print("  Creating impact area node")
    query_step_reproduce = """
    MERGE (ia:ImpactArea {impact_area: $impact_area}) RETURN ia
    """
    execute_query(driver, query_step_reproduce, {"impact_area": impact_area_text})

    # Create Fields node
    print("  Creating Fields node")
    query_description = "MERGE (f:Fields) RETURN f"
    execute_query(driver, query_description)

    # Create Relationships
    print("  Creating relationships")
    query_relationships = """
    MATCH (f:Fields), (p:Priority {priority: $priority})
    MERGE (f)-[:HAS_PRIORITY]->(p)
    WITH f
    MATCH (f), (rc:RootCause {root_cause: $root_cause})
    MERGE (f)-[:HAS_ROOT_CAUSE]->(rc)
    WITH f
    MATCH (f), (ia:ImpactArea {impact_area: $impact_area})
    MERGE (f)-[:HAS_IMPACT_AREA]->(ia)
    """
    parameters = {"priority": priority_text, "root_cause": root_cause_text, "impact_area": impact_area_text}
    execute_query(driver, query_relationships, parameters)


# Function to create comment nodes
def create_comments_node(driver, comments):
    print("Creating comments node")
    create_provider_query = """
    MERGE (c:Comments {comments: $comments})
    """
    parameters = {"comments": comments}
    execute_query(driver, create_provider_query, parameters)


# Main function to read the CSV file and populate the graph
def main():
    driver = GraphDatabase.driver(NEO4J_URI, auth=AUTH)

    with open("tickets.csv", mode="r") as file:
        reader = csv.DictReader(file)
        print("Reading CSV file...")

        for row in reader:
            code = row["Code"]
            title = row["Title"]
            summary = row["Summary"]
            issue_description = row["Issue_Description"]
            step_reproduce = row["Step_To_Reproduce"]
            priority = row["Priority"]
            root_cause = row["Root_Cause"]
            impact_area = row["Impact_Area"]
            comments = row["Comments"]

            create_ticket_node(driver, code=code, title=title)
            create_summary_node(driver, summary=summary)
            create_description_node(driver, issue_description_text=issue_description, step_reproduce_text=step_reproduce)
            create_fields_node(driver, priority_text=priority, root_cause_text=root_cause, impact_area_text=impact_area)
            create_comments_node(driver, comments=comments)

    driver.close()
    print("Graph populated successfully!")


# Run the main function
if __name__ == "__main__":
    main()
