"""
Watch the logs folder and turn every new test log into a bug ticket.

Usage:
    python watch_logs.py              # keep watching, check every 5 seconds
    python watch_logs.py --interval 30
    python watch_logs.py --once       # process new logs once, then exit

Drop a .log or .txt file into logs/ and a markdown ticket with the same name
appears in tickets/. To regenerate a ticket, delete it and it will be recreated.

If a new log shows the same issue as an existing ticket, no new ticket is
created. The log is recorded in tickets/duplicates.json and noted at the
bottom of the existing ticket instead.
"""

import argparse
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# Folders live next to this script, so it works from any working directory
BASE_DIR = Path(__file__).parent
LOGS_DIR = BASE_DIR / "logs"
TICKETS_DIR = BASE_DIR / "tickets"
DUPLICATES_FILE = TICKETS_DIR / "duplicates.json"  # duplicate log -> existing ticket
LOG_SUFFIXES = (".log", ".txt")

# Skip files changed in the last few seconds - they may still be being written
SETTLE_SECONDS = 2

MODEL = "gpt-6-luna"

system_prompt = """
You are a senior QA engineer who turns raw test failure logs into clear bug tickets.

Respond in markdown with exactly these sections:
- **Title**: one line, specific enough to find in a bug tracker
- **Summary**: no more than two sentences
- **Severity**: Critical, High, Medium or Low, with a one-line reason
- **Steps to Reproduce**: a numbered list
- **Expected Result**
- **Actual Result**
- **Likely Component**

Use only the information in the log. Do not invent details.
If information for a section is missing, write "Not provided".
Do not wrap the markdown in a code block.
"""


def user_prompt_for(log_text):
    return "Create a bug ticket from this test log.\n\n" + log_text


def create_ticket(openai, log_text):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt_for(log_text)},
    ]
    response = openai.chat.completions.create(
        model=MODEL,
        reasoning_effort="none",
        messages=messages,
    )
    return response.choices[0].message.content


duplicate_check_prompt = """
You are a senior QA engineer triaging test failures.
You get a new test failure log and the existing bug tickets.

Decide whether the new log shows the same underlying issue as one of the existing tickets.
It is the same issue if the failing behaviour and likely cause match, even when the
test run, build, user, timestamps or wording are different.
A different failure in the same feature is NOT a duplicate.

Respond in JSON only:
{"duplicate_of": "<file name of the matching ticket, or null>", "reason": "<one sentence>"}
"""


def find_duplicate(openai, log_text):
    """Return (existing ticket file, reason) if this log repeats a known issue, else (None, reason)."""
    existing_tickets = sorted(TICKETS_DIR.glob("*.md"))
    if not existing_tickets:
        return None, "no existing tickets"

    tickets_text = "\n\n".join(
        f"### {ticket.name}\n{ticket.read_text(encoding='utf-8')}" for ticket in existing_tickets
    )
    messages = [
        {"role": "system", "content": duplicate_check_prompt},
        {"role": "user", "content": f"Existing tickets:\n\n{tickets_text}\n\nNew log:\n\n{log_text}"},
    ]
    response = openai.chat.completions.create(
        model=MODEL,
        reasoning_effort="none",
        messages=messages,
        response_format={"type": "json_object"},
    )
    result = json.loads(response.choices[0].message.content)
    match = TICKETS_DIR / str(result.get("duplicate_of"))
    if result.get("duplicate_of") and match in existing_tickets:
        return match, result.get("reason", "")
    return None, result.get("reason", "")


def load_duplicates():
    if DUPLICATES_FILE.exists():
        return json.loads(DUPLICATES_FILE.read_text(encoding="utf-8"))
    return {}


def record_duplicate(log_file, ticket_file):
    """Remember the duplicate so it isn't checked again, and note it on the existing ticket."""
    duplicates = load_duplicates()
    duplicates[log_file.name] = ticket_file.name
    DUPLICATES_FILE.write_text(json.dumps(duplicates, indent=2), encoding="utf-8")
    with ticket_file.open("a", encoding="utf-8") as ticket:
        ticket.write(f"\n\n_Also seen in: {log_file.name}_\n")


def find_new_logs():
    """Return logs that haven't been handled yet and have finished being written."""
    now = time.time()
    duplicates = load_duplicates()
    new_logs = []
    for log_file in sorted(LOGS_DIR.iterdir()):
        if log_file.suffix not in LOG_SUFFIXES:
            continue
        if (TICKETS_DIR / f"{log_file.stem}.md").exists() or log_file.name in duplicates:
            continue
        if now - log_file.stat().st_mtime < SETTLE_SECONDS:
            continue
        new_logs.append(log_file)
    return new_logs


def process_new_logs(openai):
    for log_file in find_new_logs():
        ticket_file = TICKETS_DIR / f"{log_file.stem}.md"
        print(f"New log: {log_file.name} - checking for an existing ticket...")
        try:
            log_text = log_file.read_text(encoding="utf-8")
            existing_ticket, reason = find_duplicate(openai, log_text)
            if existing_ticket:
                record_duplicate(log_file, existing_ticket)
                print(f"  Duplicate of {existing_ticket.name} - no new ticket ({reason})")
                continue
            print("  New issue - creating ticket...")
            ticket = create_ticket(openai, log_text)
        except Exception as error:
            # Leave it without a ticket so it is retried on the next check
            print(f"  Failed: {error}")
            continue
        ticket_file.write_text(ticket, encoding="utf-8")
        print(f"  Saved {ticket_file.relative_to(BASE_DIR)}")


def main():
    parser = argparse.ArgumentParser(description="Turn new test logs into bug tickets.")
    parser.add_argument("--interval", type=float, default=5, help="seconds between checks (default: 5)")
    parser.add_argument("--once", action="store_true", help="process new logs once and exit")
    args = parser.parse_args()

    load_dotenv(override=True)
    if not os.getenv("OPENAI_API_KEY"):
        print("No API key found - please check your .env file")
        return

    openai = OpenAI()
    LOGS_DIR.mkdir(exist_ok=True)
    TICKETS_DIR.mkdir(exist_ok=True)

    if args.once:
        process_new_logs(openai)
        return

    print(f"Watching {LOGS_DIR} every {args.interval:g}s - press Ctrl+C to stop")
    try:
        while True:
            process_new_logs(openai)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("Stopped.")


if __name__ == "__main__":
    main()
