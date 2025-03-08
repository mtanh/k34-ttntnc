# Description: Generates 100 sample records for a ticketing system with diverse content.
# The script generates random ticket IDs, titles, summaries, issue descriptions, steps to reproduce,
# priorities, root causes, impact areas, comments, and relationships.

import random
import json

# Expanded options for diversity
priorities = ["Low", "Medium", "High", "Critical"]
root_causes = [
    "Data Issue",
    "Bug",
    "Network Failure",
    "Configuration Error",
    "User Error",
    "API Failure",
]
impact_areas = ["Strategic", "Operational", "User Experience", "Security", "Financial"]
issue_types = [
    (
        "Login failure due to timeout",
        "Multiple users unable to log in due to persistent timeout errors",
        "Since 03/05/2025 8:00 AM PST, over 200 users report login failures with 'Timeout Error 504' after entering credentials. Issue spans web and mobile platforms.",
        "1. Visit login page (https://platform.example.com/login). 2. Input credentials (e.g., jane.doe@example.com, pwd123). 3. Click 'Sign In'. 4. Wait 20 seconds. 5. See 'Timeout Error 504'. Expected: Immediate login success.",
    ),
    (
        "Profile photo upload stuck",
        "Profile photo upload process hangs indefinitely for premium users",
        "Premium users report that since 03/04/2025 3:00 PM PST, uploading a new profile photo via web stalls at 50% progress, no error shown. Affects 50+ accounts.",
        "1. Log in as premium user (https://platform.example.com). 2. Go to 'Edit Profile'. 3. Click 'Change Photo'. 4. Upload a 2MB JPG file. 5. Observe progress bar stuck at 50% after 5 minutes. Expected: Upload completes in 10 seconds.",
    ),
    (
        "API rate limit exceeded",
        "Third-party app integration fails due to API rate limit errors",
        "Developer reports that since 03/06/2025 6:00 AM PST, API calls to fetch user connections return 'Rate Limit Exceeded (429)' after 100 requests/minute, blocking app functionality.",
        "1. Set up API client with key (e.g., xyz123). 2. Make GET request to /v2/connections endpoint 100 times in 60 seconds. 3. On 101st call, see 'Rate Limit Exceeded (429)'. Expected: Successful response up to 1000 calls/minute.",
    ),
    (
        "Billing page crashes",
        "Billing dashboard crashes when viewing invoice history",
        "Admins report that since 03/03/2025 11:00 AM PST, accessing invoice history in the billing dashboard causes a page crash with 'Error 500' on Chrome and Firefox.",
        "1. Log in to admin portal (https://admin.example.com). 2. Navigate to 'Billing'. 3. Click 'View Invoice History'. 4. Select 'Past 6 Months'. 5. Observe 'Error 500' and page reload. Expected: Invoice list displays.",
    ),
    (
        "Messages not delivering",
        "Messages sent to connections not delivered for 12+ hours",
        "Users report that since 03/05/2025 9:00 PM PST, messages sent via web and mobile are marked 'Sent' but not received by recipients. Impacts 300+ users.",
        "1. Log in (https://platform.example.com). 2. Go to 'Messages'. 3. Send 'Test message' to a connection. 4. Ask recipient to check inbox after 1 hour. 5. Confirm message missing. Expected: Delivered within 1 minute.",
    ),
    (
        "Analytics report missing data",
        "Analytics dashboard shows incomplete visitor stats for recruiters",
        "Recruiters note that since 03/04/2025 7:00 AM PST, the 'Profile Visitors' report omits data for the past 3 days, showing 'No data available' despite confirmed views.",
        "1. Log in as recruiter (https://platform.example.com/recruiter). 2. Open 'Analytics'. 3. Select 'Profile Visitors' for 03/01-03/03/2025. 4. See 'No data available'. Expected: Visitor stats for 50+ views.",
    ),
    (
        "Group post visibility issue",
        "Posts in private groups not visible to members",
        "Group admins report that since 03/06/2025 10:00 AM PST, new posts in private groups (e.g., Group ID 45678) are not appearing in feeds, despite successful submission.",
        "1. Join private group (ID 45678) as member. 2. Log in (https://platform.example.com). 3. Post 'Test post' in group. 4. Refresh feed after 10 minutes. 5. Confirm post missing. Expected: Post visible instantly.",
    ),
]


# Generate ticket ID
def generate_ticket_code(index):
    return f"ENT-{23000 + index}"


# Generate relationships
def generate_relationships(ticket_id, all_ids):
    clone_from = random.sample(all_ids, 1) if random.random() > 0.7 else []
    clone_to = (
        random.sample(all_ids, random.randint(0, 2)) if random.random() > 0.8 else []
    )
    similar_to = (
        random.sample(all_ids, random.randint(0, 3)) if random.random() > 0.6 else []
    )
    return json.dumps(clone_from), json.dumps(clone_to), json.dumps(similar_to)


# Generate comments
def generate_comments():
    comment_templates = [
        {
            "user-1": "Anyone seen this before?",
            "user-2": "Logged with dev team, ETA 03/07/2025.",
        },
        {
            "user-3": "Fixed after cache clear on 03/06/2025 2:00 PM PST.",
            "user-4": "Confirmed, closing.",
        },
        {
            "user-5": "Still occurring for 10% of users.",
            "user-6": "Escalating to tier 2 support.",
        },
    ]
    return json.dumps(random.sample(comment_templates, random.randint(1, 2)))


# Generate 100 records
records = []
all_ids = [generate_ticket_code(i) for i in range(100)]

for i in range(100):
    issue = random.choice(issue_types)
    ticket_code = generate_ticket_code(i)
    title, summary, issue_desc, steps = issue
    priority = random.choice(priorities)
    root_cause = random.choice(root_causes)
    impact_area = random.choice(impact_areas)
    comments = generate_comments()
    clone_from, clone_to, similar_to = generate_relationships(
        ticket_code, [x for x in all_ids if x != ticket_code]
    )

    record = f'{ticket_code},"{title}","{summary}","{issue_desc}","{steps}","{priority}","{root_cause}","{impact_area}","{comments}","{clone_from}","{clone_to}","{similar_to}"'
    records.append(record)

# Write to CSV
with open("tickets.csv", "w") as f:
    f.write(
        "Code,Title,Summary,Issue_Description,Step_To_Reproduce,Priority,Root_Cause,Impact_Area,Comments,Clone_From,Clone_To,Similar_To\n"
    )
    f.write("\n".join(records))

print("Generated 100 records with diverse content in 'tickets.csv'")
