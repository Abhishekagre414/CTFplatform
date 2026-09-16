"""
TechCorp Employee Document Portal
---------------------------------
A deliberately vulnerable Flask application for the
"The Exposed Employee File" cybersecurity training lab (Lab 2).

INTENDED VULNERABILITY (for instructors -- do not spoil for learners):
Information Disclosure / Sensitive Data Exposure (CWE-538 / CWE-548,
OWASP A01:2021 - Broken Access Control, A05:2021 - Security
Misconfiguration).

Authentication is implemented correctly using Flask's signed server-side
session -- you cannot forge a valid login without a real password.
However, the document-serving route (/files/<path>) has TWO flaws that
are common in the real world:

  1. NO PER-RESOURCE AUTHORIZATION.  Once a user is authenticated, the
     route serves ANY file under the documents/ store without checking
     that the requested folder actually belongs to that user.  Files are
     loaded purely from a predictable path such as:

         /files/EMP1042/profile.txt

     The employee number and file name are guessable, so a learner can
     change the path and read documents that are not theirs.

  2. DIRECTORY LISTING IS ENABLED.  Requesting a folder path (e.g.
     /files/ or /files/hr/) returns an index of its contents instead of
     denying the request.  This leaks the existence and names of
     sensitive internal files.

Together these let an authenticated employee walk back from their own
document URL to /files/, discover an internal HR folder that was never
linked in the UI, and read a sensitive salary report containing the flag:

         TECHCORP{hidden_file_found}

This models the lesson that authentication alone does NOT make every
resource safe to expose -- sensitive resources still need proper
authorization and secure storage.

SAFETY: the file server is sandboxed to this app's own documents/
directory.  Path traversal outside the sandbox (../, absolute paths) is
rejected, so the lab is exploitable only against its own fictional data
on localhost.  No real personal or company data is used.
"""

import os
import sqlite3
import logging
import re
from datetime import datetime, timezone
from functools import wraps

from flask import (
    Flask, request, redirect, url_for, render_template,
    session, g, make_response, jsonify, Response, abort
)
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "techcorp.db")
DOCS_DIR = os.path.join(BASE_DIR, "documents")

app = Flask(__name__)
app.secret_key = os.environ.get("LAB_SECRET_KEY", "techcorp-lab2-dev-secret-key-change-me")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# The flag lives ONLY inside this exposed sensitive document (created on
# disk by init_docs()).  It is not present in any template, static asset,
# comment served to the learner, or the README.
THE_FLAG = "TECHCORP{hidden_file_found}"

# The learner's own employee folder + the sensitive folder they must find.
LEARNER_EMP_ID = "EMP1042"
SENSITIVE_REL_PATH = os.path.join("hr", "employee_salary_report.txt")

# Server-side scoring. Each milestone is awarded once per lab session.
# The client never supplies or controls the score.
SCORE_VALUES = {
    "login_completed": 10,
    "documents_explored": 10,
    "other_employee_document": 20,
    "directory_listing_discovered": 15,
    "hr_repository_discovered": 15,
    "sensitive_document_accessed": 20,
    "flag_submitted": 10,
}
MAX_SCORE = sum(SCORE_VALUES.values())


def get_score():
    """Return the server-calculated score and milestone state."""
    milestones = session.get("score_milestones", {})
    if not isinstance(milestones, dict):
        milestones = {}
    score = sum(points for name, points in SCORE_VALUES.items() if milestones.get(name))
    return score, {name: bool(milestones.get(name, False)) for name in SCORE_VALUES}


def award_milestone(name):
    """Award a milestone once. The event is triggered only by backend actions."""
    if name not in SCORE_VALUES:
        return False
    milestones = session.get("score_milestones", {})
    if not isinstance(milestones, dict):
        milestones = {}
    if milestones.get(name):
        return False
    milestones[name] = True
    session["score_milestones"] = milestones
    session.modified = True
    log.info("SCORING: milestone=%s +%d user=%s", name, SCORE_VALUES[name], session.get("username"))
    return True


def reset_scoring():
    session["score_milestones"] = {}
    session["flag_captured"] = False
    session["knowledge_check_passed"] = False

# ----------------------------------------------------------------------
# Logging (for learner + instructor visibility of what's happening)
# ----------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("techcorp-lab2")


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
        DROP TABLE IF EXISTS mission_progress;

        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT NOT NULL,
            role TEXT NOT NULL,
            department TEXT NOT NULL,
            employee_id TEXT NOT NULL
        );

        CREATE TABLE mission_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_owner TEXT NOT NULL,
            current_mission INTEGER NOT NULL DEFAULT 1,
            flag_captured INTEGER NOT NULL DEFAULT 0,
            knowledge_check_passed INTEGER NOT NULL DEFAULT 0
        );
        """
    )

    users = [
        ("alex", "Alex@123", "Alex Turner", "employee", "IT Support", LEARNER_EMP_ID),
        ("sarah", "Sarah@123", "Sarah Nguyen", "manager", "Security Team", "EMP1007"),
        ("hradmin", "Hr@12345", "Priya Rao", "hr", "Human Resources", "EMP1001"),
    ]
    for username, pw, display_name, role, dept, emp_id in users:
        cur.execute(
            "INSERT INTO users (username, password_hash, display_name, role, department, employee_id) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (username, generate_password_hash(pw), display_name, role, dept, emp_id),
        )

    conn.commit()
    conn.close()
    log.info("Database initialized with fresh lab data.")


# ----------------------------------------------------------------------
# Document store setup (creates the fictional files on disk)
# ----------------------------------------------------------------------
def init_docs():
    """Create the fictional document store. All data is invented for the lab."""
    # Learner's own documents (linked in the portal UI).
    emp_dir = os.path.join(DOCS_DIR, LEARNER_EMP_ID)
    # Another employee's folder -- reinforces that IDs are predictable.
    emp2_dir = os.path.join(DOCS_DIR, "EMP1043")
    # The sensitive internal folder that was NEVER meant to be reachable.
    hr_dir = os.path.join(DOCS_DIR, "hr")

    for d in (emp_dir, emp2_dir, hr_dir):
        os.makedirs(d, exist_ok=True)

    files = {
        os.path.join(emp_dir, "profile.txt"):
            "TECHCORP EMPLOYEE PROFILE\n"
            "=========================\n\n"
            "Name:        Alex Turner\n"
            "Employee ID: EMP1042\n"
            "Department:  IT Support\n"
            "Manager:     Sarah Nguyen (Security Team)\n"
            "Start Date:  2026-01-15\n\n"
            "Your documents are stored under /files/EMP1042/.\n"
            "For questions about company records, contact Human Resources.\n",

        os.path.join(emp_dir, "training.pdf"):
            "TECHCORP SECURITY AWARENESS TRAINING - COMPLETION RECORD\n\n"
            "Employee: Alex Turner (EMP1042)\n"
            "Module:   Handling Sensitive Information\n"
            "Status:   COMPLETED\n"
            "Score:    94%\n\n"
            "Reminder: never store confidential files in shared or\n"
            "predictable locations. Report anything that looks exposed.\n",

        os.path.join(emp_dir, "payslip.pdf"):
            "TECHCORP PAYSLIP\n\n"
            "Employee: Alex Turner (EMP1042)\n"
            "Period:   August 2026\n"
            "Net Pay:  (sample lab data - not real)\n\n"
            "This document is intended only for the named employee.\n",

        os.path.join(emp2_dir, "profile.txt"):
            "TECHCORP EMPLOYEE PROFILE\n"
            "=========================\n\n"
            "Name:        Jordan Blake\n"
            "Employee ID: EMP1043\n"
            "Department:  Finance\n\n"
            "(You are viewing a document that does not belong to your\n"
            " account. Notice how little stopped you from opening it.)\n",

        # ---- The sensitive, unlinked file that holds the flag ----
        os.path.join(hr_dir, "employee_salary_report.txt"):
            "TECHCORP - CONFIDENTIAL / INTERNAL HR USE ONLY\n"
            "===============================================\n"
            "CONSOLIDATED EMPLOYEE SALARY REPORT (FY2026)\n\n"
            "This file must NOT be published on the employee portal.\n"
            "It was left in a predictable, unprotected path by mistake.\n\n"
            "  EMP1001  Priya Rao       Human Resources   (sample data)\n"
            "  EMP1007  Sarah Nguyen    Security Team      (sample data)\n"
            "  EMP1042  Alex Turner     IT Support         (sample data)\n"
            "  EMP1043  Jordan Blake    Finance            (sample data)\n\n"
            "All figures above are fictional lab data.\n\n"
            "If you can read this file as a normal employee, the portal\n"
            "has an Information Disclosure vulnerability.\n\n"
            f"FLAG: {THE_FLAG}\n",

        os.path.join(hr_dir, "README.txt"):
            "INTERNAL HR ARCHIVE\n\n"
            "Restricted. Files in this folder are for Human Resources only\n"
            "and should never be reachable from the employee portal.\n",
    }

    for path, content in files.items():
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    log.info("Document store initialized under documents/.")


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


# ----------------------------------------------------------------------
# Safe path resolution -- keeps the lab exploitable only within its own
# documents/ sandbox. Real filesystem traversal (../, absolute paths) is
# rejected so the vulnerability stays logical and non-destructive.
# ----------------------------------------------------------------------
def resolve_in_sandbox(subpath):
    """
    Resolve a requested path against DOCS_DIR.
    Returns an absolute path inside the sandbox, or None if the request
    would escape it. NOTE: this deliberately does NOT check whether the
    resource belongs to the current user -- that missing check is the
    intended vulnerability.
    """
    subpath = (subpath or "").strip()
    # Reject obvious traversal / absolute paths outright.
    if subpath.startswith("/") or ".." in subpath.replace("\\", "/").split("/"):
        return None
    candidate = os.path.normpath(os.path.join(DOCS_DIR, subpath))
    docs_root = os.path.normpath(DOCS_DIR)
    # Confirm the resolved path is still inside the sandbox.
    if candidate != docs_root and not candidate.startswith(docs_root + os.sep):
        return None
    return candidate


# ----------------------------------------------------------------------
# Mission / progress helpers (session-based for MVP)
# ----------------------------------------------------------------------
def get_progress():
    if "mission" not in session:
        session["mission"] = 1
    if "flag_captured" not in session:
        session["flag_captured"] = False
    return session["mission"], session["flag_captured"]


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
        reset_scoring()


def complete_lab_session():
    if session.get("lab_started_at") and not session.get("lab_completed_at"):
        session["lab_completed_at"] = datetime.now(timezone.utc).isoformat()
    session["lab_status"] = "completed"


# ----------------------------------------------------------------------
# Route: Lab shell (TryHackMe-style split view)
# ----------------------------------------------------------------------
@app.route("/")
def index():
    """Renders the single-page lab shell: task/questions panel on the left,
    a simulated desktop environment (with an embedded browser) on the right."""
    return render_template("lab.html")


@app.route("/api/state")
def api_state():
    """Lightweight state the front-end uses to reflect progress in the task panel."""
    user = get_current_user()
    score, milestones = get_score()
    return jsonify({
        "logged_in": bool(user),
        "username": user["username"] if user else None,
        "role": user["role"] if user else None,
        "lab_status": session.get("lab_status", "not_started"),
        "mission": int(session.get("mission", 1)),
        "flag_captured": bool(session.get("flag_captured", False)),
        "knowledge_check_passed": bool(session.get("knowledge_check_passed", False)),
        "score": score,
        "max_score": MAX_SCORE,
        "score_milestones": milestones,
        "elapsed_seconds": lab_elapsed_seconds(),
    })


@app.route("/api/start-lab", methods=["POST"])
def api_start_lab():
    start_lab_session()
    score, milestones = get_score()
    return jsonify({"status": "running", "score": score, "max_score": MAX_SCORE, "score_milestones": milestones, "elapsed_seconds": lab_elapsed_seconds()})


@app.route("/api/submit-flag", methods=["POST"])
def api_submit_flag():
    data = request.get_json(silent=True) or {}
    submitted = str(data.get("flag") or "").strip()

    # The learner must first actually retrieve the exposed sensitive file.
    # Once that has happened, the flag is validated server-side with an
    # exact comparison.
    exposed = bool(session.get("flag_captured", False))
    correct = exposed and submitted == THE_FLAG

    if correct:
        session["flag_captured"] = True
        set_mission(5)
        award_milestone("flag_submitted")

    score, milestones = get_score()
    return jsonify({
        "correct": correct,
        "exploited": exposed,
        "score": score,
        "max_score": MAX_SCORE,
        "score_milestones": milestones,
        "message": (
            "Correct flag."
            if correct
            else (
                "Find and open the exposed sensitive file first."
                if not exposed
                else "Incorrect flag."
            )
        ),
    })


@app.route("/api/knowledge-check", methods=["POST"])
def api_knowledge_check():
    data = request.get_json(silent=True) or {}
    disclosure_answer = (data.get("disclosure_answer") or "").lower()
    control_answer = (data.get("control_answer") or "").lower()
    summary = (data.get("summary") or "").strip()

    # Validate the concepts, not a single exact sentence.
    disclosure_patterns = [
        r"\bexpos\w*\b", r"\bdisclos\w*\b", r"\bleak\w*\b",
        r"\bsensitive\b", r"\bunauthori[sz]\w*\b", r"\breveal\w*\b",
    ]
    control_patterns = [
        r"\bauthori[sz]\w*\b", r"\baccess\s+control\w*\b", r"\bpermission\w*\b",
        r"\bacl\b", r"\brestrict\w*\b", r"\bauthenticat\w*\b",
        r"\bprivat\w*\b", r"\bencrypt\w*\b", r"\bnon-?predictable\b",
        r"\brandom\w*\b", r"\bstor\w*\b",
    ]

    disclosure_ok = any(re.search(p, disclosure_answer) for p in disclosure_patterns)
    control_ok = any(re.search(p, control_answer) for p in control_patterns)
    summary_words = re.findall(r"\b\w+\b", summary)
    summary_ok = len(summary_words) >= 8

    passed = disclosure_ok and control_ok and summary_ok and bool(session.get("flag_captured", False))
    session["knowledge_check_passed"] = passed
    if passed:
        set_mission(6)
        complete_lab_session()
    score, milestones = get_score()
    return jsonify({
        "passed": passed,
        "disclosure_ok": disclosure_ok,
        "control_ok": control_ok,
        "summary_ok": summary_ok,
        "flag_captured": bool(session.get("flag_captured", False)),
        "score": score,
        "max_score": MAX_SCORE,
        "score_milestones": milestones,
    })


@app.route("/api/lab/score")
def api_lab_score():
    """Read-only server-side score endpoint. Never accepts a client score."""
    score, milestones = get_score()
    return jsonify({"score": score, "max_score": MAX_SCORE, "completed": session.get("lab_status") == "completed", "milestones": milestones})


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
            # Preserve the lab session while replacing only the authentication
            # identity (so the timer/progress aren't reset by login).
            lab_state = {
                key: session.get(key)
                for key in (
                    "lab_started_at", "lab_completed_at", "lab_status",
                    "mission", "flag_captured", "knowledge_check_passed", "score_milestones",
                )
                if key in session
            }

            session.clear()
            session.update(lab_state)
            session["user_id"] = user["id"]
            session["username"] = user["username"]

            if session.get("lab_status") == "running":
                set_mission(2)
                award_milestone("login_completed")

            log.info(f"Login success: {username} (role={user['role']})")
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


@app.route("/documents")
@login_required
def documents():
    user = get_current_user()
    if session.get("lab_status") == "running":
        set_mission(3)
        award_milestone("documents_explored")
    # The portal only advertises the current employee's own documents.
    my_docs = ["profile.txt", "training.pdf", "payslip.pdf"]
    return render_template(
        "documents.html",
        user=user,
        emp_id=user["employee_id"],
        my_docs=my_docs,
    )


# --- VULNERABLE FILE SERVER -------------------------------------------
# Serves documents purely by predictable path, with NO check that the
# requested folder belongs to the authenticated user, and with directory
# listing ENABLED. Both are intentional flaws for the lab.
@app.route("/files/")
@app.route("/files/<path:subpath>")
@login_required
def files(subpath=""):
    target = resolve_in_sandbox(subpath)
    if target is None or not os.path.exists(target):
        return render_template("error.html", message="File or directory not found."), 404

    # ---- Directory listing (Security Misconfiguration) ----
    if os.path.isdir(target):
        if session.get("lab_status") == "running":
            # Browsing a directory index counts as discovering exposed metadata.
            set_mission(4)
            award_milestone("directory_listing_discovered")
            rel_here = os.path.relpath(target, DOCS_DIR).replace(os.sep, "/")
            if rel_here.lower().startswith("hr"):
                award_milestone("hr_repository_discovered")
        entries = []
        for name in sorted(os.listdir(target)):
            full = os.path.join(target, name)
            rel = os.path.relpath(full, DOCS_DIR).replace(os.sep, "/")
            entries.append({
                "name": name + ("/" if os.path.isdir(full) else ""),
                "href": url_for("files", subpath=rel) + ("/" if os.path.isdir(full) else ""),
                "is_dir": os.path.isdir(full),
            })
        # Build a "parent" link unless we're already at the root.
        parent = None
        rel_here = os.path.relpath(target, DOCS_DIR).replace(os.sep, "/")
        if rel_here not in (".", ""):
            up = "/".join(rel_here.split("/")[:-1])
            parent = url_for("files", subpath=up) + ("/" if up else "")
        display = "/files/" + (rel_here + "/" if rel_here not in (".", "") else "")
        return render_template("listing.html", display=display, entries=entries, parent=parent)

    # ---- File download / view (missing authorization) ----
    rel_target = os.path.relpath(target, DOCS_DIR).replace(os.sep, "/")
    if session.get("lab_status") == "running":
        # Reading another employee's document is a meaningful discovery step.
        first_segment = rel_target.split("/", 1)[0] if rel_target else ""
        if first_segment.startswith("EMP") and first_segment != LEARNER_EMP_ID:
            award_milestone("other_employee_document")

    if os.path.normpath(rel_target) == os.path.normpath(SENSITIVE_REL_PATH):
        # The learner reached the exposed sensitive file -> record success.
        if session.get("lab_status") == "running":
            session["flag_captured"] = True
            set_mission(5)
            award_milestone("sensitive_document_accessed")
        log.info(
            "VULNERABILITY TRIGGERED: authenticated user "
            f"'{session.get('username')}' read sensitive file '{rel_target}' "
            "via predictable path (information disclosure)."
        )

    with open(target, "rb") as f:
        content = f.read()

    ext = os.path.splitext(target)[1].lower()
    mimetype = {
        ".txt": "text/plain",
        ".pdf": "text/plain",   # served as text so the lab data is readable in-browser
        ".csv": "text/plain",
        ".log": "text/plain",
    }.get(ext, "application/octet-stream")
    return Response(content, mimetype=mimetype)


@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", message="Page not found."), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("error.html", message="Internal server error."), 500


# ----------------------------------------------------------------------
# Lab reset endpoint (safe: only touches this app's own DB + docs + session)
# ----------------------------------------------------------------------
@app.route("/lab/reset", methods=["POST"])
def lab_reset():
    init_db()
    init_docs()
    session.clear()
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        init_db()
    init_docs()  # always refresh the fictional document store on start
    app.run(host="127.0.0.1", port=5000, debug=False)
