# Description: Enriches the ticket data by adding random relationships between tickets
# The relationships are stored in the Clone_From, Clone_To, and Similar_To fields

import csv
import json
import random

# Path to the input and output CSV files
INPUT_CSV_PATH = "tickets_50.csv"
OUTPUT_CSV_PATH = "tickets_50.clock"


def load_tickets_from_csv(file_path):
    tickets = []
    with open(file_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            tickets.append(row)
    return tickets


def generate_random_tickets(current_code, total_tickets, min_refs=1, max_refs=3):
    # Generate a list of all ticket codes (ENT-23000 to ENT-23199)
    all_codes = [f"ENT-{i:05d}" for i in range(23000, 23200)]
    # Remove the current ticket code to avoid self-reference
    all_codes.remove(current_code)
    # Randomly select between min_refs and max_refs tickets
    num_refs = random.randint(min_refs, max_refs)
    selected_codes = random.sample(all_codes, min(num_refs, len(all_codes)))
    return selected_codes


def update_relationships(tickets):
    for ticket in tickets:
        current_code = ticket["Code"]

        # Parse existing JSON fields (if any)
        clone_from = json.loads(ticket["Clone_From"]) if ticket["Clone_From"] else []
        clone_to = json.loads(ticket["Clone_To"]) if ticket["Clone_To"] else []
        similar_to = json.loads(ticket["Similar_To"]) if ticket["Similar_To"] else []

        # Add new random references while preserving existing ones
        new_clone_from = clone_from + generate_random_tickets(current_code, 200)
        new_clone_to = clone_to + generate_random_tickets(current_code, 200)
        new_similar_to = similar_to + generate_random_tickets(current_code, 200)

        # Remove duplicates and limit to a reasonable number (e.g., max 5 references per field)
        ticket["Clone_From"] = json.dumps(list(dict.fromkeys(new_clone_from))[:5])
        ticket["Clone_To"] = json.dumps(list(dict.fromkeys(new_clone_to))[:5])
        ticket["Similar_To"] = json.dumps(list(dict.fromkeys(new_similar_to))[:5])


def save_updated_tickets(tickets):
    fieldnames = tickets[0].keys()
    with open(OUTPUT_CSV_PATH, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(tickets)


def main():
    # Load tickets from CSV
    tickets = load_tickets_from_csv(INPUT_CSV_PATH)

    # Update relationships
    update_relationships(tickets)

    # Save updated tickets to a new CSV file
    save_updated_tickets(tickets)
    print(f"Updated tickets saved to {OUTPUT_CSV_PATH}")


if __name__ == "__main__":
    main()
