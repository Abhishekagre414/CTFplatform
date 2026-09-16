# The Exposed Employee File
### TechCorp Employee Document Portal — Cybersecurity Training Lab (Lab 2)

## Lab Purpose

This is a beginner-friendly, self-contained cybersecurity training lab that teaches
**Information Disclosure** (also called **Sensitive Data Exposure**): how sensitive files end
up reachable when an application serves documents from predictable paths without proper access
controls.

You'll play as **Alex Turner**, a Junior Cybersecurity Analyst at TechCorp, investigating why
internal files are appearing on an employee document portal that should only show each employee
their own documents.

This lab is intentionally vulnerable **only within this project**. It runs entirely on your
local machine (e.g., Kali Linux) with no external dependencies.

## Learning Objectives

By completing this lab, you will practice and understand:

- What Information Disclosure / Sensitive Data Exposure means
- How predictable file paths and URLs lead to exposure
- Why directory listing is a dangerous misconfiguration
- Using browser Developer Tools to inspect requests
- Basic Kali/Linux investigation habits
- Why sensitive files require authorization and secure storage

**Authentication** = Who are you?
**Authorization** = What are you allowed to access?

Being logged in does **not** mean every file on the server is safe to hand you.

## Requirements

- A Linux machine (tested on Kali Linux)
- Python 3.9+
- Firefox (or any browser)
- Browser DevTools (Burp Suite optional)
- No internet access required

## Installation

```bash
cd techcorp-info-disclosure
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

Or simply run:

```bash
chmod +x start.sh
./start.sh
```

The application will be available at: **http://127.0.0.1:5000**

Opening that URL loads a TryHackMe-style split view:
- **Left panel** — the story, missions, hints, flag submission, and knowledge check.
- **Right panel** — a simulated desktop environment. Double-click the **Firefox** icon (or use
  "Open Browser") to launch the actual vulnerable portal inside a browser-style window. A
  **Terminal** icon is available for notes/flavor (use your own terminal/DevTools for real
  traffic).

## How the Storyline Works

The lab is structured as a 5-mission investigation:

1. **Log In to the Portal** — Authenticate as a normal employee.
2. **Explore the Documents** — View your own files and watch the URLs.
3. **Inspect the File Paths** — Study how documents are loaded; try folders, not just files.
4. **Find the Exposed File** — Reach the sensitive document you were never meant to see and
   capture the flag.
5. **Explain the Incident** — Reflect on what happened.

A final **Knowledge Check** asks you to explain Information Disclosure and the control that
prevents it before the lab is marked complete.

You'll only be given an **Employee** account. Discovering the exposure is part of the exercise —
progressive hints are available in Mission 3 if you get stuck.

## Resetting the Lab

```bash
./reset.sh
```

This deletes and recreates the lab's local SQLite database and its `documents/` store only. It
does not touch anything outside this project folder.

## Notes

- This application deliberately contains a security flaw for educational purposes. Do not deploy
  it outside of an isolated local training environment.
- The vulnerability, exploitation path, and flag are documented separately for instructors in
  `INSTRUCTOR.md` — that file is not meant to be read before attempting the lab.
- All employee data in this lab is fictional. No real personal or company data is used.

## Scoring

The lab uses a server-side 100-point scoring system. Each milestone is awarded once per lab session:

- Login successfully — **10 points**
- Explore My Documents — **10 points**
- Read another employee's exposed document — **20 points**
- Discover the exposed directory listing — **15 points**
- Discover the HR repository — **15 points**
- Read the sensitive HR document — **20 points**
- Submit the correct flag — **10 points**

**Maximum score: 100 points.** The score is calculated by Flask on the server; the browser cannot submit an arbitrary score. Starting a fresh lab or resetting the lab clears the score.
