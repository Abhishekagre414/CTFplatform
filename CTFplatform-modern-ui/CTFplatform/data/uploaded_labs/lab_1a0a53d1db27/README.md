# Lab 4 — The Strange Support Ticket

Topic: Reflected XSS
Difficulty: Beginner
Environment: TechCorp Support Desk

## Run with Docker

    docker compose up --build

Open http://localhost:5004

## Run without Docker

    pip install -r requirements.txt
    python app/app.py

Open http://127.0.0.1:5000

## Story flow

Briefing -> Mission 1 -> Mission 2 -> Mission 3 -> Mission 4 -> Mission 5 -> Flag

The vulnerable endpoint is `/lab?message=...`. It intentionally reflects the
message into the HTML response for this isolated training lab.

Use only the harmless payload supplied by the lab:

    <script>alert('TechCorp XSS Lab')</script>

Do not test it against real websites.
