# Description: This script generates a diverse sample of 100 ticket records with unique
# content for each field. The records are saved in a CSV file 'tickets.csv'

import csv
import random
from datetime import datetime
from datetime import timedelta
import json

codes = [f"ENT-{23000 + i}" for i in range(100)]  # Changed from 2000 to 100
priorities = ["Critical", "High", "Medium", "Low", "Urgent"]
root_causes = [
    "Network Failure",
    "Database Corruption",
    "Authentication Bug",
    "Server Crash",
    "API Rate Limit",
    "Cache Inconsistency",
    "Memory Leak",
    "Config Error",
    "Third-Party Outage",
    "Disk Space Full",
    "Queue Overflow",
]
impact_areas = [
    "Operational",
    "User Experience",
    "Billing System",
    "Performance Metrics",
    "Data Integrity",
    "Security Layer",
    "Customer Portal",
    "Analytics Dashboard",
]
users = [f"user-{i}" for i in range(1, 30)]

title_phrases = [
    "Login fails abruptly",
    "Payment stalls unexpectedly",
    "Chat drops suddenly",
    "Dashboard breaks often",
    "Email halts intermittently",
    "Search fails consistently",
    "Sync lags repeatedly",
    "Reports vanish randomly",
    "Notifications stop silently",
    "Profile freezes quickly",
    "Tickets close automatically",
    "Checkout fails instantly",
    "Session ends abruptly",
    "Export hangs quietly",
    "Form crashes silently",
    "Reset stalls slowly",
    "List disappears oddly",
    "Billing freezes randomly",
    "Analytics lag heavily",
    "Chat drops frequently",
    "Invoice fails quietly",
    "Search crashes fast",
    "History vanishes suddenly",
    "Settings fail instantly",
    "App stops suddenly",
    "API times out",
    "Uploads stall often",
    "Comments vanish quickly",
    "Refresh hangs silently",
    "Alerts stop abruptly",
    "Login delays heavily",
    "Payment lags slowly",
    "Dashboard loads partially",
    "Email sends late",
    "Search returns empty",
    "Sync fails quietly",
    "Orders drop randomly",
    "Users lock out",
    "Reports load slowly",
    "Files corrupt easily",
    "Links break often",
    "Forms reset unexpectedly",
    "Cache clears itself",
    "Data sync stalls",
    "Alerts fail silently",
    "Profiles load blank",
    "Payments reject fast",
    "Chats disconnect often",
]
summary_modifiers = [
    "suddenly",
    "repeatedly",
    "intermittently",
    "consistently",
    "in peak hours",
    "during update",
    "for new users",
    "on mobile",
    "with errors",
    "across regions",
    "in batches",
    "under load",
    "at night",
    "during login",
    "after reboot",
    "on weekends",
    "in background",
    "with high usage",
    "post-migration",
    "during sync",
    "on refresh",
    "after logout",
]
desc_starts = [
    "Multiple customers report",
    "System intermittently fails when",
    "Users complain about",
    "Critical feature degrades after",
    "Service disruption began",
    "Unexpected behavior occurs if",
    "Support tickets spike due to",
    "Platform crashes during",
]
desc_issues = [
    "accessing account settings",
    "processing large transactions",
    "handling multiple requests",
    "rendering complex pages",
    "syncing external data",
    "validating user input",
    "exporting report data",
    "uploading media files",
    "resetting passwords",
    "loading user profiles",
    "generating invoices",
    "searching products",
    "updating settings",
    "viewing order history",
    "sending notifications",
    "processing refunds",
    "displaying analytics",
    "managing tickets",
]
step_actions = [
    "Sign in with",
    "Navigate to section",
    "Click button for",
    "Try submitting",
    "Upload file via",
    "Refresh page after",
    "Modify settings in",
    "Test feature with",
    "Simulate load on",
    "Open link from",
    "Switch to mode",
    "Enter data in",
    "Export report from",
    "Search using filter",
    "Reset via form",
    "View history in",
    "Send message from",
    "Update profile with",
]
step_contexts = [
    "new user account",
    "existing customer profile",
    "admin dashboard",
    "mobile interface",
    "peak traffic period",
    "test environment",
    "production system",
    "guest checkout",
    "legacy browser",
    "high-volume scenario",
    "low-bandwidth network",
    "multi-user session",
    "offline mode",
    "cross-device setup",
    "single sign-on",
    "batch processing",
]


def generate_unique_content(used_content, field_type, ticket_id):
    if field_type == "Title":
        base = random.choice(title_phrases)
        content = f"{base} {ticket_id}"
        if len(content.split()) > 10:
            content = " ".join(content.split()[:10])
        if content not in used_content[field_type]:
            used_content[field_type].add(content)
            return content
    else:
        base_content = ""
        if field_type == "Summary":
            base_content = (
                f"{random.choice(title_phrases)} {random.choice(summary_modifiers)}. "
                f"This issue disrupts normal operations across multiple critical systems daily affecting productivity. "
                f"Users face persistent delays impacting their ability to complete essential tasks efficiently. "
                f"Problem manifests repeatedly during high usage periods causing widespread dissatisfaction among clients. "
                f"Support teams observe a surge in complaints requiring urgent technical intervention immediately. "
                f"Current mitigation efforts have proven ineffective needing advanced troubleshooting and resources now."
            )
        elif field_type == "Issue_Description":
            date_str = (datetime.now() - timedelta(days=random.randint(0, 7))).strftime(
                "%m/%d/%Y %I:%M %p"
            )
            affected = random.choice(
                [
                    f"{random.randint(5, 200)} users",
                    f"{random.randint(1, 50)}% of traffic",
                    "specific regions",
                ]
            )
            base_content = (
                f"{random.choice(desc_starts)} {random.choice(desc_issues)} {random.choice(['since', 'after', 'around'])} {date_str}. "
                f"Affects {affected}. {random.choice(['No logs available', 'Shows timeout', 'Partial data loss'])}. "
                f"This problem severely hampers user productivity across various platform functionalities daily. "
                f"Repeated failures frustrate customers who depend on timely system responses consistently. "
                f"Issue persists in multiple environments necessitating comprehensive investigation and resolution now."
            )
        else:  # Step_To_Reproduce
            base_content = (
                f"1. {random.choice(step_actions)} {random.choice(step_contexts)}. "
                f"2. Go to '{random.choice(['Account', 'Billing', 'Support', 'Reports'])}'. "
                f"3. {random.choice(step_actions)} {random.choice(['feature', 'form', 'data'])}. "
                f"4. Use {random.choice(['invalid', 'large', 'special'])} input. "
                f"5. Note {random.choice(['crash', 'delay', 'error'])} after {random.randint(1, 15)} sec. "
                f"Ensure proper authentication before starting this process to replicate accurately always. "
                f"Test during varying conditions to confirm issue consistency across scenarios fully now. "
                f"Record all observed behaviors meticulously for detailed support team analysis immediately."
            )

        while len(base_content.split()) < 100:
            base_content += (
                f" Additional {random.choice(['testing', 'monitoring', 'debugging'])} "
                f"reveals {random.choice(['inconsistent', 'persistent', 'escalating'])} "
                f"behavior affecting {random.choice(['performance', 'reliability', 'usability'])}. "
                f"This requires {random.choice(['immediate', 'thorough', 'specialized'])} "
                f"{random.choice(['attention', 'resources', 'expertise'])} to resolve effectively now."
            )

        content = f"{base_content} Ticket {ticket_id} specific."
        if content not in used_content[field_type]:
            used_content[field_type].add(content)
            return content

    return None


def generate_random_ticket(ticket_id, used_content):
    code = f"ENT-{23000 + ticket_id}"
    title = generate_unique_content(used_content, "Title", ticket_id)
    if not title:
        raise Exception("Could not generate unique Title")

    summary = generate_unique_content(used_content, "Summary", ticket_id)
    if not summary:
        raise Exception("Could not generate unique Summary")

    desc = generate_unique_content(used_content, "Issue_Description", ticket_id)
    if not desc:
        raise Exception("Could not generate unique Issue_Description")

    steps = generate_unique_content(used_content, "Step_To_Reproduce", ticket_id)
    if not steps:
        raise Exception("Could not generate unique Step_To_Reproduce")

    priority = random.choice(priorities)
    root_cause = random.choice(root_causes)
    impact_area = random.choice(impact_areas)

    comment_users = random.sample(users, random.randint(3, 5))
    comment_options = [
        f"Confirmed in {random.choice(['prod', 'dev', 'QA'])} env",
        f"Affects {random.randint(1, 50)}% of attempts",
        f"Workaround: {random.choice(['restart service', 'clear cache', 'use backup'])}",
        f"Related to {random.choice(['update', 'migration', 'outage'])} yesterday",
        f"Escalated to {random.choice(['dev team', 'vendor', 'ops'])}",
        f"Logs show {random.choice(['null pointer', 'timeout', '500 error'])}",
    ]
    comments = [{u: random.choice(comment_options)} for u in comment_users]

    ref_options = lambda: f"ENT-{23000 + random.randint(0, 99)}"  # Changed range from 1999 to 99
    clone_from = (
        [ref_options() for _ in range(random.randint(0, 2))]
        if random.random() > 0.6
        else []
    )
    clone_to = (
        [ref_options() for _ in range(random.randint(0, 2))]
        if random.random() > 0.6
        else []
    )
    similar_to = (
        [ref_options() for _ in range(random.randint(0, 2))]
        if random.random() > 0.6
        else []
    )

    return {
        "Code": code,
        "Title": title,
        "Summary": summary,
        "Issue_Description": desc,
        "Step_To_Reproduce": steps,
        "Priority": priority,
        "Root_Cause": root_cause,
        "Impact_Area": impact_area,
        "Comments": json.dumps(comments),
        "Clone_From": json.dumps(clone_from),
        "Clone_To": json.dumps(clone_to),
        "Similar_To": json.dumps(similar_to),
    }


used_content = {
    "Title": set(),
    "Summary": set(),
    "Issue_Description": set(),
    "Step_To_Reproduce": set(),
}

records = []
for i in range(100):  # Changed from 200 to 100
    try:
        record = generate_random_ticket(i, used_content)
        records.append(record)
    except Exception as e:
        print(f"Error at record {i}: {e}")
        break

headers = [
    "Code",
    "Title",
    "Summary",
    "Issue_Description",
    "Step_To_Reproduce",
    "Priority",
    "Root_Cause",
    "Impact_Area",
    "Comments",
    "Clone_From",
    "Clone_To",
    "Similar_To",
]

with open("tickets_100.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=headers)
    writer.writeheader()
    writer.writerows(records)

print(
    f"Generated {len(records)} diverse sample records with unique content in 'tickets_100.csv'"
)