# The Missing Employee Access Control
### TechCorp Employee Management Portal — Cybersecurity Training Lab (Lab 3)

## Lab Purpose

This is a beginner-friendly, self-contained cybersecurity training lab that teaches
**IDOR (Insecure Direct Object Reference)** — what happens when an application uses a
user-controlled identifier to select an object without checking whether the user is
actually authorized to access it.

You'll play as **Alex Turner**, a Junior Cybersecurity Analyst at TechCorp, investigating a
report that employees can view *other* employees' profiles simply by changing a number in the
URL of the internal Employee Management Portal.

This lab is intentionally vulnerable **only within this project**. It is designed to run entirely
on your local machine (e.g., Kali Linux) with no external dependencies.

## Learning Objectives

By completing this lab, you will practice and understand:

- What IDOR (Insecure Direct Object Reference) means
- The relationship between object IDs and authorization
- How to recognize user-controlled identifiers in URLs
- Why changing an ID can expose another user's data
- Basic web-application investigation using browser tools
- How proper server-side authorization prevents IDOR

**Authentication** = Who are you?
**Authorization** = Are you allowed to access *this specific object*?

## Requirements

- A Linux machine (tested on Kali Linux)
- Python 3.9+
- Firefox (or any browser)
- Browser DevTools (Burp Suite is optional — not required for this lab)
- No internet access required

## Installation

```bash
cd techcorp-idor
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
  "Open Browser" in the left panel) to launch the actual vulnerable portal inside a browser-style
  window. A **Terminal** icon is also available for note-taking (it does not execute real
  commands — use your own terminal for real traffic inspection).

## Starting the Lab

1. Run `./start.sh` (or the manual steps above).
2. Open the lab at `http://127.0.0.1:5000` and press **Start Lab**.
3. Follow the on-screen story and missions — the lab will guide you step by step.

## Resetting the Lab

If you want to start over from a clean state at any time:

```bash
./reset.sh
```

This deletes and recreates the lab's local SQLite database only. It does not touch anything
outside this project folder. You can also reset from within the app using the **Reset Lab**
button.

## How the Storyline Works

The lab is structured as a 5-mission investigation:

1. **Log In as an Employee** — Authenticate with the provided account.
2. **Inspect Your Own Profile** — Open your profile and study its URL.
3. **Follow the Evidence** — Identify the user-controlled employee ID in the URL.
4. **The Unlocked Record** — Reach another employee's profile and capture the flag.
5. **Explain the Incident** — Reflect on why the authorization check was missing.

A final **Knowledge Check** asks you to explain IDOR in your own words before the lab is marked
complete.

You will only be given an **Employee** account. Discovering the vulnerability is part of the
exercise — no exploit steps are spelled out for you directly, but progressive hints are available
in Mission 3 if you get stuck.

## How to Test the Lab

A good end-to-end test run looks like:

1. Start the app and open it in the browser.
2. Log in with the Employee credentials shown in Mission 1.
3. Open **My Profile** and note the URL (`/profile/101`).
4. Change the trailing number and try another employee's record.
5. Confirm you can view a profile that is not your own, and find the flag inside it.
6. Submit the flag in Mission 4.
7. Complete Mission 5 and the Knowledge Check.
8. Try `./reset.sh` and confirm the lab returns to its original state.

## Notes

- This application deliberately contains a security flaw for educational purposes. Do not deploy
  it outside of an isolated local training environment.
- The vulnerability, exploitation path, and flag are documented separately for
  instructors in `INSTRUCTOR.md` — that file is not meant to be read before attempting the lab.
- All employee data in this lab is fictional.
