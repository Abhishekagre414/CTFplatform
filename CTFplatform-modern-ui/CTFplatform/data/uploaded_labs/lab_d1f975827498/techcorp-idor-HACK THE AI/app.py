"""
TechCorp Employee Management Portal
------------------------------------
A deliberately vulnerable Flask application for the
"The Missing Employee Access Control" cybersecurity training lab (Lab 3).

INTENDED VULNERABILITY (for instructors - do not spoil for learners):
Authentication is implemented correctly using Flask's signed server-side
session. However, the profile page at /profile/<emp_id> looks the record up
purely from the numeric employee ID supplied in the URL and NEVER checks
whether the authenticated user is authorised to view that particular record.

Because the object reference (the employee ID) is directly user-controlled,
a learner logged in as Alex (emp_id 101) can simply change:

    /profile/101   ->   /profile/102

...and the server will happily return a different employee's private profile.
This models a very common real-world bug class: Insecure Direct Object
Reference (IDOR) - trusting a user-supplied identifier to select an object
without an accompanying server-side authorisation check.

This app is intentionally isolated, non-destructive, and only exploitable
against itself on localhost.
"""

import os
import sqlite3
import logging
import re
from datetime import datetime, timezone
from functools import wraps

from flask import (
    Flask, request, redirect, url_for, render_template,
    session, g, make_response, jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "techcorp.db")

app = Flask(__name__)
app.secret_key = os.environ.get("LAB_SECRET_KEY", "techcorp-lab-dev-secret-key-change-me")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# ----------------------------------------------------------------------
# Logging (for learner + instructor visibility of what's happening)
# ----------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("techcorp-lab")


@app.before_request
def log_request():
    safe_cookies = {k: ("[REDACTED]" if k == "session" else v) for k, v in request.cookies.items()}
    log.info(f"{request.method} {request.path} | cookies={safe_cookies}")


# ----------------------------------------------------------------------
# Database helpers
# ----------------------------------------------------------------------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    os.makedirs(os.path.join(BASE_DIR, "database"), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript(
        """
        DROP TABLE IF EXISTS users;

        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id INTEGER UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT NOT NULL,
            role TEXT NOT NULL,
            department TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            profile_flag TEXT
        );
        """
    )

    # emp_id, username, password, display_name, role, department, email, phone, flag
    # Only "alex" (101) is handed to the learner. The flag lives in Rahul's
    # record (102), reachable only by changing the object reference in the URL.
    THE_FLAG = "TECHCORP{idor_found}"
    users = [
        (101, "alex", "Alex@123", "Alex Turner", "employee", "IT Support",
         "alex.turner@techcorp.local", "+1-555-0101", None),
        (102, "rahul", "Rahul@123", "Rahul Sharma", "employee", "Finance",
         "rahul.sharma@techcorp.local", "+1-555-0102", THE_FLAG),
        (103, "priya", "Priya@123", "Priya Nair", "employee", "Marketing",
         "priya.nair@techcorp.local", "+1-555-0103", None),
        (104, "sarah", "Sarah@123", "Sarah Nguyen", "manager", "Security Team",
         "sarah.nguyen@techcorp.local", "+1-555-0104", None),
        (105, "admin", "Admin@123", "System Administrator", "administrator", "IT Administration",
         "it.admin@techcorp.local", "+1-555-0105", None),
    ]
    for emp_id, username, pw, display_name, role, dept, email, phone, flag in users:
        cur.execute(
            "INSERT INTO users (emp_id, username, password_hash, display_name, role, "
            "department, email, phone, profile_flag) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (emp_id, username, generate_password_hash(pw), display_name, role, dept, email, phone, flag),
        )

    conn.commit()
    conn.close()
    log.info("Database initialized with fresh lab data.")


# ----------------------------------------------------------------------
# Auth helpers
# ----------------------------------------------------------------------
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def get_current_user():
    """The AUTHENTICATED user, looked up from the trusted server-side session."""
    user_id = session.get("user_id")
    if not user_id:
        return None
    db = get_db()
    return db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def get_user_by_emp_id(emp_id):
    db = get_db()
    return db.execute("SELECT * FROM users WHERE emp_id = ?", (emp_id,)).fetchone()


# ----------------------------------------------------------------------
# Mission / progress helpers (simple, session-based for MVP)
# ----------------------------------------------------------------------
def set_mission(n):
    session["mission"] = max(int(session.get("mission", 1)), n)


def lab_elapsed_seconds():
    """Return server-tracked elapsed lab time. The browser never controls this clock."""
    started = session.get("lab_started_at")
    if not started:
        return 0
    try:
        start = datetime.fromisoformat(started)
        end = session.get("lab_completed_at")
        finish = datetime.fromisoformat(end) if end else datetime.now(timezone.utc)
        return max(0, int((finish - start).total_seconds()))
    except (TypeError, ValueError):
        return 0


def start_lab_session():
    if not session.get("lab_started_at") or session.get("lab_completed_at"):
        session["lab_started_at"] = datetime.now(timezone.utc).isoformat()
        session.pop("lab_completed_at", None)
        session["lab_status"] = "running"


def complete_lab_session():
    if session.get("lab_started_at") and not session.get("lab_completed_at"):
        session["lab_completed_at"] = datetime.now(timezone.utc).isoformat()
    session["lab_status"] = "completed"


# ----------------------------------------------------------------------
# Route: Lab shell (TryHackMe-style split view)
# ----------------------------------------------------------------------
THE_FLAG = "TECHCORP{idor_found}"


@app.route("/")
def index():
    """Renders the single-page lab shell: task/questions panel on the left,
    a simulated desktop environment (with an embedded browser) on the right."""
    return render_template("lab.html")


@app.route("/api/state")
def api_state():
    """Lightweight state the front-end uses to reflect progress in the task panel."""
    user = get_current_user()
    return jsonify({
        "logged_in": bool(user),
        "username": user["username"] if user else None,
        "role": user["role"] if user else None,
        "emp_id": user["emp_id"] if user else None,
        "lab_status": session.get("lab_status", "not_started"),
        "mission": int(session.get("mission", 1)),
        "flag_captured": bool(session.get("flag_captured", False)),
        "knowledge_check_passed": bool(session.get("knowledge_check_passed", False)),
        "elapsed_seconds": lab_elapsed_seconds(),
    })


@app.route("/api/start-lab", methods=["POST"])
def api_start_lab():
    start_lab_session()
    return jsonify({"status": "running", "elapsed_seconds": lab_elapsed_seconds()})


@app.route("/api/submit-flag", methods=["POST"])
def api_submit_flag():
    data = request.get_json(silent=True) or {}
    submitted = str(data.get("flag") or "").strip()

    # The learner must first demonstrate the vulnerability (access a profile
    # that is not their own). Only then is the flag validated server-side with
    # an exact comparison.
    exploited = bool(session.get("flag_captured", False))
    correct = exploited and submitted == THE_FLAG

    if correct:
        session["flag_captured"] = True
        set_mission(4)

    return jsonify({
        "correct": correct,
        "exploited": exploited,
        "message": (
            "Correct flag."
            if correct
            else (
                "Access another employee's profile through the ID in the URL first."
                if not exploited
                else "Incorrect flag."
            )
        ),
    })


@app.route("/api/knowledge-check", methods=["POST"])
def api_knowledge_check():
    data = request.get_json(silent=True) or {}
    concept_answer = (data.get("concept_answer") or "").lower()
    prevent_answer = (data.get("prevent_answer") or "").lower()
    summary = (data.get("summary") or "").strip()

    # Validate the concepts, not a single exact sentence. This accepts natural
    # answers while avoiding accidental substring matches.
    concept_patterns = [
        r"\bobject\b", r"\breference\b", r"\bidentifier\b", r"\bid\b",
        r"\bdirect\b", r"\bidor\b",
    ]
    prevent_patterns = [
        r"\bauthori[sz]\w*\b", r"\baccess\s+control\b", r"\bpermission\w*\b",
        r"\bserver[- ]side\b", r"\bverif\w*\b", r"\bowner\w*\b",
        r"\bcheck\w*\b", r"\ballow\w*\b", r"\bright\w*\b",
    ]

    concept_ok = any(re.search(p, concept_answer) for p in concept_patterns)
    prevent_ok = any(re.search(p, prevent_answer) for p in prevent_patterns)
    summary_words = re.findall(r"\b\w+\b", summary)
    summary_ok = len(summary_words) >= 8

    passed = concept_ok and prevent_ok and summary_ok and bool(session.get("flag_captured", False))
    session["knowledge_check_passed"] = passed
    if passed:
        set_mission(5)
        complete_lab_session()
    return jsonify({
        "passed": passed,
        "concept_ok": concept_ok,
        "prevent_ok": prevent_ok,
        "summary_ok": summary_ok,
        "flag_captured": bool(session.get("flag_captured", False)),
    })


# ----------------------------------------------------------------------
# Routes: Authentication
# ----------------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            # Preserve the lab session (timer, missions, flag) while replacing
            # only the authentication identity.
            lab_state = {
                key: session.get(key)
                for key in (
                    "lab_started_at", "lab_completed_at", "lab_status",
                    "mission", "flag_captured", "knowledge_check_passed",
                )
                if key in session
            }

            # --- Authentication uses the secure, signed session. ---
            session.clear()
            session.update(lab_state)
            session["user_id"] = user["id"]
            session["username"] = user["username"]

            if session.get("lab_status") == "running":
                set_mission(2)

            log.info(f"Login success: {username} (emp_id={user['emp_id']}, role={user['role']})")
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid username or password."
            log.info(f"Login failed for username='{username}'")

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ----------------------------------------------------------------------
# Routes: Portal pages
# ----------------------------------------------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    user = get_current_user()
    if session.get("lab_status") == "running" and user:
        set_mission(3)
    return render_template("dashboard.html", user=user)


@app.route("/profile")
@login_required
def my_profile():
    """Convenience redirect to the authenticated user's own profile."""
    user = get_current_user()
    return redirect(url_for("profile", emp_id=user["emp_id"]))


# --- VULNERABLE OBJECT LOOKUP -----------------------------------------
# This route selects the record purely from the user-controlled emp_id in the
# URL. It authenticates (login_required) but performs NO authorisation check
# that the logged-in user is allowed to view THIS particular profile. That
# missing check is the IDOR.
@app.route("/profile/<int:emp_id>")
@login_required
def profile(emp_id):
    current = get_current_user()
    target = get_user_by_emp_id(emp_id)  # <-- direct object reference, no ownership check

    if target is None:
        return render_template("error.html", message=f"No employee found with ID {emp_id}."), 404

    is_own = (target["emp_id"] == current["emp_id"])

    # Successful exploitation path: the authenticated user is viewing a record
    # that is not their own. This proves the missing authorisation check.
    if not is_own:
        if session.get("lab_status") == "running":
            session["flag_captured"] = True
            set_mission(4)
        log.info(
            f"VULNERABILITY TRIGGERED: user '{current['username']}' (emp_id="
            f"{current['emp_id']}) accessed profile emp_id={target['emp_id']} "
            f"('{target['display_name']}') via IDOR"
        )

    return render_template(
        "profile.html",
        user=current,
        target=target,
        is_own=is_own,
        show_flag=bool(target["profile_flag"]),
    )


@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", message="Page not found."), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("error.html", message="Internal server error."), 500


# ----------------------------------------------------------------------
# Lab reset endpoint (safe: only touches this app's own SQLite DB + session)
# ----------------------------------------------------------------------
@app.route("/lab/reset", methods=["POST"])
def lab_reset():
    init_db()
    session.clear()
    return make_response(jsonify({"status": "ok"}))


if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        init_db()
    app.run(host="127.0.0.1", port=5000, debug=False)
