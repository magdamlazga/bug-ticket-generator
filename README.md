# Bug Ticket Generator

Turns raw automated-test failure logs into clear, structured bug tickets using an LLM.

## Why this exists

In most software teams, automated regression suites run every night and produce a pile of failure logs by morning. Someone, usually a QA engineer, then has to read each log, work out what actually went wrong, judge how serious it is and write it up as a ticket developers can act on. That triage is repetitive, slow and inconsistent: tickets vary in quality depending on who wrote them and how busy they were, and important failures can sit unreported while the team works through the noise.

This project automates that first step. A failed test log goes in and a ready-to-review bug ticket comes out, always in the same format and always with a severity call. The benefits:

- **Time saved:** QA engineers review and refine tickets instead of writing every one from scratch.
- **Faster feedback:** failures become tickets developers can pick up minutes after a test run, not hours.
- **Consistency:** every ticket has the same sections, so tickets are easier to search, compare and prioritise.
- **No made-up details:** the model may only use what is in the log, and marks anything missing as "Not provided" so a human knows what to check.

I built it as a hands-on LLM engineering project, applying what I learned to a real problem from software testing.

## What a ticket looks like

Each ticket follows the same format: **Title, Summary, Severity, Steps to Reproduce, Expected Result, Actual Result, Likely Component**. The model is told to use only what is in the log and to write "Not provided" instead of inventing details.

## How it works

```
logs/checkout_saved_card.log   ──►   LLM   ──►   tickets/checkout_saved_card.md
```

- Drop a `.log` or `.txt` file into `logs/`.
- Any log without a matching ticket in `tickets/` gets one generated.
- Logs that already have a ticket are skipped, so nothing is sent to the API twice.
- To regenerate a ticket, delete it from `tickets/`.

## Duplicate detection

The same bug often fails several tests, or fails again in the next night's run, so different log files can describe one issue. Before creating a ticket, `watch_logs.py` asks the LLM to compare the new log with the existing tickets. It counts as the same issue when the failing behaviour and likely cause match, even if the test, build, user or timestamps differ.

When a duplicate is found:
- No new ticket is created.
- The existing ticket gets an _"Also seen in: <log file>"_ line, so you can see how often an issue occurs.
- The log is recorded in `tickets/duplicates.json` so it isn't checked again. To re-check a log, remove its entry from that file.

Example: `guest_checkout_payment.log` comes from a different test, browser and pipeline, but it fails with the same payment gateway timeout as `checkout_saved_card.log`. It gets linked to the existing ticket instead of creating a second one.

## Two ways to run it

| File | What it does |
|------|--------------|
| `ticket_creation.ipynb` | Interactive version: run the cell to process all new logs and see the tickets rendered in the notebook. |
| `watch_logs.py` | Automated version: keeps running and creates a ticket as soon as a new log appears in `logs/`, skipping logs that repeat a known issue. |

```bash
python watch_logs.py              # watch the folder, check every 5 seconds
python watch_logs.py --interval 30
python watch_logs.py --once       # process new logs once and exit
```

The watcher waits until a file hasn't changed for a couple of seconds before reading it, so half-written logs aren't picked up. If an API call fails, the log is retried on the next check.

## Setup

Requires Python 3.12+ with `openai` and `python-dotenv`, and an `OPENAI_API_KEY` in a `.env` file.

## Sample data

`logs/` contains five made-up failure logs to try it out: checkout payment timeout, password reset, search with special characters, mobile basket badge, and a guest checkout log that is a duplicate of the checkout payment timeout.
