# Description: This script reads the CSV file and populates the graph database with the data.
# It creates nodes for tickets, summaries, issue descriptions, steps to reproduce, priorities,
# root causes, impact areas, and comments.
# It also establishes relationships between these nodes.
# The script uses the Neo4j Python driver to connect to the database and execute Cypher queries.

from dotenv import load_dotenv
import os
import csv
import json
from neo4j import GraphDatabase

load_dotenv()

AURA_INSTANCENAME = os.environ["AURA_INSTANCENAME"]
NEO4J_URI = os.environ["NEO4J_URI"]
NEO4J_USERNAME = os.environ["NEO4J_USERNAME"]
NEO4J_PASSWORD = os.environ["NEO4J_PASSWORD"]
NEO4J_DATABASE = os.environ["NEO4J_DATABASE"]
AUTH = (NEO4J_USERNAME, NEO4J_PASSWORD)

driver = GraphDatabase.driver(NEO4J_URI, auth=AUTH, database=NEO4J_DATABASE)

CSV_FILE_NAME = os.environ["CSV_FILE_NAME"]


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


# Function to create issue description nodes
def create_issue_description_node(driver, issue_description_text):
    print("Creating issue description node")
    create_provider_query = """
    MERGE (id:IssueDescription {description: $description})
    """
    parameters = {"description": issue_description_text}
    execute_query(driver, create_provider_query, parameters)


# Function to create step to reproduce nodes
def create_step_reproduce_node(driver, step_reproduce_text):
    print("Creating step to reproduce node")
    create_provider_query = """
    MERGE (sr:StepReproduce {step: $step})
    """
    parameters = {"step": step_reproduce_text}
    execute_query(driver, create_provider_query, parameters)


# Function to create priority nodes
def create_priority_node(driver, priority_text):
    print("Creating priority node")
    create_provider_query = """
    MERGE (p:Priority {priority: $priority})
    """
    parameters = {"priority": priority_text}
    execute_query(driver, create_provider_query, parameters)


# Function to create root cause nodes
def create_root_cause_node(driver, root_cause_text):
    print("Creating root cause node")
    create_provider_query = """
    MERGE (rc:RootCause {root_cause: $root_cause})
    """
    parameters = {"root_cause": root_cause_text}
    execute_query(driver, create_provider_query, parameters)


# Function to create impact area nodes
def create_impact_area_node(driver, impact_area_text):
    print("Creating impact area node")
    create_provider_query = """
    MERGE (ia:ImpactArea {impact_area: $impact_area})
    """
    parameters = {"impact_area": impact_area_text}
    execute_query(driver, create_provider_query, parameters)


# Function to create comment nodes
def create_comments_node(driver, comments):
    print("Creating comments node")
    create_provider_query = """
    MERGE (c:Comments {comments: $comments})
    """
    parameters = {"comments": comments}
    execute_query(driver, create_provider_query, parameters)


# Function to create intra-issue tree
def create_intra_issue_tree(
    driver,
    code,
    title,
    summary,
    issue_description,
    steps_reproduce,
    priority,
    root_cause,
    impact_area,
    comments,
):
    print("Creating ticket relationships")
    create_relationships_query = """
    MATCH (t:Ticket {code: $code, title: $title}), (s:Summary {summary: $summary})
    MERGE (t)-[:HAS_SUMMARY]->(s)
    WITH t
    MATCH (t), (id:IssueDescription {description: $description})
    MERGE (t)-[:HAS_ISSUE_DESCRIPTION]->(id)
    WITH t
    MATCH (t), (sr:StepReproduce {step: $step})
    MERGE (t)-[:HAS_STEPS_TO_REPRODUCE]->(sr)
    WITH t
    MATCH (t), (p:Priority {priority: $priority})
    MERGE (t)-[:HAS_PRIORITY]->(p)
    WITH t
    MATCH (t), (rc:RootCause {root_cause: $root_cause})
    MERGE (t)-[:HAS_ROOT_CAUSE]->(rc)
    WITH t
    MATCH (t), (ia:ImpactArea {impact_area: $impact_area})
    MERGE (t)-[:HAS_IMPACT_AREA]->(ia)
    WITH t
    MATCH (t), (c:Comments {comments: $comments})
    MERGE (t)-[:HAS_COMMENTS]->(c)
    """
    parameters = {
        "code": code,
        "title": title,
        "summary": summary,
        "description": issue_description,
        "step": steps_reproduce,
        "priority": priority,
        "root_cause": root_cause,
        "impact_area": impact_area,
        "comments": comments,
    }
    execute_query(driver, create_relationships_query, parameters)


# Function to create clone from relationship
def create_clone_from_relationship(driver, code, clone_from_code):
    print("Creating clone from relationship")
    with driver.session() as session:
        session.run(
            "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Ticket) REQUIRE t.code IS UNIQUE"
        )

    create_clone_query = """
                        MATCH (t1:Ticket {code: $code1})
                        MATCH (t2:Ticket {code: $code2})
                        MERGE (t1)-[:CLONE_FROM]->(t2)
                        """
    parameters = {"code1": code, "code2": clone_from_code}
    execute_query(driver, create_clone_query, parameters)


# Function to create clone to relationship
def create_clone_to_relationship(driver, code, clone_to_code):
    print("Creating clone to relationship")
    with driver.session() as session:
        session.run(
            "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Ticket) REQUIRE t.code IS UNIQUE"
        )

    create_clone_query = """
                        MATCH (t1:Ticket {code: $code1})
                        MATCH (t2:Ticket {code: $code2})
                        MERGE (t1)-[:CLONE_TO]->(t2)
                        """
    parameters = {"code1": code, "code2": clone_to_code}
    execute_query(driver, create_clone_query, parameters)


# Function to create similar to relationship
def create_similar_to_relationship():
    print("Creating similar to relationship")
    driver = GraphDatabase.driver(NEO4J_URI, auth=AUTH)

    with driver.session() as session:
        session.run(
            "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Ticket) REQUIRE t.code IS UNIQUE"
        )

    with open(CSV_FILE_NAME, mode="r") as file:
        reader = csv.DictReader(file)
        print("Reading CSV file...")

        for row in reader:
            code = row["Code"]
            similar_to = json.loads(row["Similar_To"])

            for st in similar_to:
                create_similar_query = """
                        MATCH (t1:Ticket {code: $code1})
                        MATCH (t2:Ticket {code: $code2})
                        MERGE (t1)-[:SIMILAR_TO]->(t2)
                        MERGE (t2)-[:SIMILAR_TO]->(t1)
                        """
                parameters = {"code1": code, "code2": st}
                execute_query(driver, create_similar_query, parameters)

    driver.close()


# Main function to read the CSV file and populate the graph
def main():
    driver = GraphDatabase.driver(NEO4J_URI, auth=AUTH)

    with open(CSV_FILE_NAME, mode="r") as file:
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
            clone_from = json.loads(row["Clone_From"])
            clone_to = json.loads(row["Clone_To"])
            # similar_to = json.loads(row["Similar_To"])

            create_ticket_node(driver, code=code, title=title)
            create_summary_node(driver, summary=summary)
            create_issue_description_node(
                driver, issue_description_text=issue_description
            )
            create_step_reproduce_node(driver, step_reproduce_text=step_reproduce)
            create_priority_node(driver, priority_text=priority)
            create_root_cause_node(driver, root_cause_text=root_cause)
            create_impact_area_node(driver, impact_area_text=impact_area)
            create_comments_node(driver, comments=comments)
            create_intra_issue_tree(
                driver,
                code=code,
                title=title,
                summary=summary,
                issue_description=issue_description,
                steps_reproduce=step_reproduce,
                priority=priority,
                root_cause=root_cause,
                impact_area=impact_area,
                comments=comments,
            )

            for cf in clone_from:
                create_clone_from_relationship(driver, code=code, clone_from_code=cf)

            for ct in clone_to:
                create_clone_to_relationship(driver, code=code, clone_to_code=ct)

    driver.close()

    # Create the similar relationship at the end
    # to make sure all node was created, because
    # it is bi-direct connection.
    create_similar_to_relationship()

    print("Graph populated successfully!")


# Run the main function
if __name__ == "__main__":
    main()
