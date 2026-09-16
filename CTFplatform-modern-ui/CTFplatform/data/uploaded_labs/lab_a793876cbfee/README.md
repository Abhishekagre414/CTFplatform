# Lab 5 — The Suspicious Email

Topic: Phishing & Social Engineering
Difficulty: Beginner
Environment: TechCorp Mail Center

## Run with Docker

    docker compose up --build

Open http://localhost:5005

## Run without Docker

    pip install -r requirements.txt
    python app/app.py

Open http://127.0.0.1:5000

## Story flow

Briefing -> Mission 1 -> Mission 2 -> Mission 3 -> Mission 4 -> Mission 5 -> Flag

The Mail Center at `/lab` is a fully simulated inbox. No real emails are
sent or received, and no links navigate anywhere — clicking the training
link only opens an inline "link inspector" panel comparing the displayed
text to the real destination.

This lab teaches learners to recognize the human-facing signs of phishing:
urgency, mismatched links, unexpected requests, and the value of MFA and
reporting.
