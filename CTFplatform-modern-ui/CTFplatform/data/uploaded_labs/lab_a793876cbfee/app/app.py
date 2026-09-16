from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = "techcorp-lab5-training-key"

MISSIONS = [
    {
        "id": 1,
        "title": "Mission 1 — Inspect the Message",
        "story": """A few days later, Alex receives another message from Sarah.

> Sarah: “We've noticed several employees receiving suspicious emails. Nobody has confirmed whether they're real or fake. I want you to investigate before someone clicks the wrong link.”

Alex opens the TechCorp Mail Center.

He finds several messages. Some are legitimate. Others look suspicious.

One email says:

“URGENT: Your TechCorp account will be disabled today!”

Another says:

“Congratulations! You have been selected for a company reward. Click here immediately.”

Alex realizes this isn't a technical vulnerability like the previous investigations.

This time, the employee is part of the security system.

Alex opens the suspicious email and notices several warning signs:

• Urgent language
• Threat of account suspension
• Unexpected request
• Suspicious link

Sarah asks:

> Sarah: “What is the first thing that makes this message suspicious?”""",
        "task": "Open the suspicious email in the Mail Center and identify the warning signs listed above.",
        "quiz": "What is suspicious?",
        "options": ["Urgency", "Font choice", "Signature color", "File size"],
        "answer": "Urgency",
        "hint": "The message pressures you to act immediately, without time to think."
    },
    {
        "id": 2,
        "title": "Mission 2 — Inspect the Link",
        "story": """Alex moves his mouse over the link.

Instead of immediately clicking it, he examines where the link would lead.

The displayed text looks legitimate. But the actual destination looks different.

Sarah reminds him:

> Sarah: “Never trust a link just because the text looks familiar.”

Alex compares:

Displayed text
      ↓
Actual URL""",
        "task": "In the Mail Center, hover over the link in the suspicious email and compare the displayed text to the actual URL shown in the link inspector.",
        "quiz": "What should you inspect?",
        "options": ["URL", "Font", "Subject line", "Signature"],
        "answer": "URL",
        "hint": "Links can display one thing and point somewhere completely different."
    },
    {
        "id": 3,
        "title": "Mission 3 — Human Firewall",
        "story": """Sarah gives Alex five fictional messages.

The learner must classify each one as LEGITIMATE or PHISHING:

Message A — “Your weekly team meeting is scheduled for 10:00 AM.”
→ LEGITIMATE

Message B — “URGENT! Verify your account within 10 minutes or it will be deleted.”
→ PHISHING

Message C — “Your requested training document is ready.”
→ LEGITIMATE

Message D — “Congratulations! Claim your reward by logging in immediately.”
→ PHISHING

Message E — “Reminder: Security awareness training starts tomorrow.”
→ LEGITIMATE

This introduces an important beginner concept: people are part of cybersecurity.""",
        "task": "Try classifying each message in the Mail Center as Legitimate or Phishing, then answer who is responsible for spotting it first.",
        "quiz": "Who detects phishing first?",
        "options": ["User", "Firewall", "Antivirus", "Server"],
        "answer": "User",
        "hint": "Before any tool reacts, a person reads the message first."
    },
    {
        "id": 4,
        "title": "Mission 4 — Build the Attack Chain",
        "story": """Now Sarah wants Alex to understand what could happen if an employee falls for the message.

The learner receives five puzzle blocks:

Attacker
   ↓
Fake Message
   ↓
Victim
   ↓
Fake Login Page
   ↓
Credential Theft

The learner must place them in the correct order.

This teaches the basic idea of a phishing attack chain without requiring the learner to build a real phishing website.""",
        "task": "Review the attack chain in the Mail Center and put the five stages in the correct order.",
        "quiz": "What is targeted?",
        "options": ["Credentials", "Printer", "Wi-Fi password", "Ticket number"],
        "answer": "Credentials",
        "hint": "The fake login page exists to capture something the victim types in."
    },
    {
        "id": 5,
        "title": "Mission 5 — Stop the Attack",
        "story": """Alex identifies the phishing email.

Sarah asks:

> Sarah: “What should an employee do next?”

The learner chooses the safest actions:

✅ Don't click suspicious links
✅ Verify through a trusted channel
✅ Report the message
✅ Use MFA
❌ Enter credentials into a suspicious page""",
        "task": "Review the safe actions in the Mail Center and identify which control adds extra protection even if a password is stolen.",
        "quiz": "What adds account protection?",
        "options": ["MFA", "Longer email subject", "Bigger font", "Auto-reply"],
        "answer": "MFA",
        "hint": "Multi-Factor Authentication adds a second step beyond just a password."
    }
]

@app.route("/")
def index():
    return render_template("index.html", missions=MISSIONS, completed=session.get("completed", []))

@app.post("/api/mission/<int:mission_id>")
def complete_mission(mission_id):
    if mission_id < 1 or mission_id > len(MISSIONS):
        return jsonify(ok=False, error="Unknown mission"), 404

    data = request.get_json(silent=True) or {}
    answer = str(data.get("answer", "")).strip()
    mission = MISSIONS[mission_id - 1]

    if answer.lower() != mission["answer"].lower():
        return jsonify(ok=False, message="Not quite. Review the evidence and try again.", hint=mission["hint"])

    completed = list(session.get("completed", []))
    if mission_id not in completed:
        completed.append(mission_id)
    session["completed"] = completed

    all_done = len(completed) == len(MISSIONS)
    return jsonify(
        ok=True,
        mission=mission_id,
        all_done=all_done,
        flag="TECHCORP{human_firewall}" if all_done else None
    )

@app.post("/reset")
def reset():
    session.clear()
    return redirect(url_for("index"))

@app.route("/lab")
def mail_center():
    # Simulated Mail Center: no real emails are sent or received.
    # All messages, senders, and links are fictional training content.
    return render_template("mail_center.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
