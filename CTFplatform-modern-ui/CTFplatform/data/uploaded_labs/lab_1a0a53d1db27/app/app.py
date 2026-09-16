from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = "techcorp-lab4-training-key"

MISSIONS = [
    {
        "id": 1,
        "title": "Mission 1 — Explore the Support Desk",
        "story": """Alex has finished investigating the employee profile issue.

The next morning, Sarah contacts him again.

> Sarah: “The Employee Portal is working better now, but our Support Desk is showing some strange ticket messages. I want you to investigate how ticket messages are displayed.”

Alex opens the new TechCorp Support Desk.

Employees can create support tickets such as:

• Printer not working
• Password reset request
• VPN connection problem

Everything looks normal.

But Alex notices that the ticket system displays information entered by employees directly on the webpage.

Sarah gives him a simple warning:

> Sarah: “Whenever an application displays user input, don't assume that input is safe.”

Alex's task is to investigate what happens when specially crafted input is submitted.""",
        "task": "Open the ticket system, read several tickets, identify where the ticket title and message appear, and notice how the application displays user-supplied information.",
        "quiz": "Where is the ticket message displayed?",
        "options": ["Database", "Browser", "Network cable", "Operating system"],
        "answer": "Browser",
        "hint": "Think about where the employee can see the rendered ticket."
    },
    {
        "id": 2,
        "title": "Mission 2 — Find User-Controlled Input",
        "story": """Alex creates a test ticket.

He notices that the ticket contains information entered directly by the employee.

Sarah gives Alex a clue:

> Sarah: “If the user can control it, investigate how the application handles it.”""",
        "task": "Identify the ticket title, the ticket message, the user-controlled input, and where the input appears after submission.",
        "quiz": "Who controls the ticket message?",
        "options": ["The user", "Only the database", "The browser vendor", "The network administrator"],
        "answer": "The user",
        "hint": "The employee supplies the message."
    },
    {
        "id": 3,
        "title": "Mission 3 — Test the Input",
        "story": """Alex wants to know whether the application treats the submitted message as ordinary text or interprets special browser content.

He performs a harmless test inside the training environment.

The application produces an unexpected browser-side result.""",
        "task": "Submit the provided safe test input, observe the result, determine where the unexpected behavior occurs, and record your evidence.",
        "quiz": "Where does the test execute?",
        "options": ["Browser", "Database", "DNS server", "Keyboard firmware"],
        "answer": "Browser",
        "hint": "XSS is a client-side browser execution problem."
    },
    {
        "id": 4,
        "title": "Mission 4 — Follow the Evidence",
        "story": """Alex opens Developer Tools.

He compares:

Input
  ↓
Server
  ↓
Webpage
  ↓
Browser

He realizes that the important question isn't just:

“What did I enter?”

It is:

“How did the application handle what I entered?”""",
        "task": "Use Developer Tools to determine where the input appears, how the response contains the input, and how the browser processes the resulting page.",
        "quiz": "Where does XSS execute?",
        "options": ["Browser", "Database", "Server rack", "DNS resolver"],
        "answer": "Browser",
        "hint": "The server reflects the data; the browser interprets the resulting page."
    },
    {
        "id": 5,
        "title": "Mission 5 — Fix the Problem",
        "story": """Alex reports the finding to Sarah.

> Alex: “The problem isn't simply that users can enter text. The problem is that the application doesn't safely handle untrusted input before displaying it.”

Sarah asks:

> Sarah: “What should the developer do?”

Alex investigates possible fixes.""",
        "task": "Choose the best security control.",
        "quiz": "Best basic defense?",
        "options": ["Encoding", "Disabling the monitor", "Changing the ticket number", "Restarting the browser"],
        "answer": "Encoding",
        "hint": "Treat untrusted output as data, not executable markup."
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
        flag="TECHCORP{xss_ticket_found}" if all_done else None
    )

@app.post("/reset")
def reset():
    session.clear()
    return redirect(url_for("index"))

@app.route("/lab")
def support_desk():
    # INTENTIONAL VULNERABILITY: isolated reflected XSS training endpoint.
    message = request.args.get("message", "")
    return render_template("support_desk.html", message=message)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
