import json
import os
import sqlite3
from contextlib import closing
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False
DATABASE = os.environ.get("COSMOS_DATABASE", os.path.join(os.path.dirname(__file__), "cosmos_facts.db"))
VALID_STATUSES = {"pending", "verified", "false", "misleading", "unknown"}
VALID_CATEGORIES = {"physics", "biology", "astronomy", "health", "technology", "earth science", "chemistry", "mathematics", "other"}


def get_db_connection():
    conn = sqlite3.connect(DATABASE, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DATABASE)), exist_ok=True)
    with closing(get_db_connection()) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS claims (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                claim_text TEXT NOT NULL,
                verification_status TEXT NOT NULL DEFAULT 'pending',
                sources TEXT NOT NULL DEFAULT '[]',
                author TEXT NOT NULL DEFAULT 'Anonymous',
                engagement INTEGER NOT NULL DEFAULT 0,
                category TEXT NOT NULL DEFAULT 'other',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS myths (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                myth_title TEXT NOT NULL,
                myth_description TEXT NOT NULL DEFAULT '',
                debunked_explanation TEXT NOT NULL,
                scientific_evidence TEXT NOT NULL DEFAULT '',
                sources TEXT NOT NULL DEFAULT '[]',
                author TEXT NOT NULL DEFAULT 'Anonymous',
                engagement INTEGER NOT NULL DEFAULT 0,
                category TEXT NOT NULL DEFAULT 'other',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS quiz_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                claim_id INTEGER, myth_id INTEGER,
                question TEXT NOT NULL, answer TEXT NOT NULL,
                difficulty TEXT DEFAULT 'medium', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        for table in ("claims", "myths"):
            columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
            if "category" not in columns:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN category TEXT NOT NULL DEFAULT 'other'")
        conn.commit()


def parse_sources(value):
    if isinstance(value, list):
        sources = value
    elif isinstance(value, str):
        value = value.strip()
        if not value:
            return []
        try:
            parsed = json.loads(value)
            sources = parsed if isinstance(parsed, list) else value.split(",")
        except json.JSONDecodeError:
            sources = value.split(",")
    else:
        sources = []
    result = []
    for item in sources:
        if isinstance(item, str) and item.strip():
            url = item.strip()
            if url.startswith(("https://", "http://")):
                result.append(url)
            else:
                result.append(url)
    return result


def clean_text(value, max_length=5000):
    return value.strip()[:max_length] if isinstance(value, str) else ""


def list_records(table, status=None, category=None, search=None):
    conditions, values = [], []
    if status and table == "claims":
        conditions.append("verification_status = ?")
        values.append(status)
    if category:
        conditions.append("lower(category) = lower(?)")
        values.append(category)
    if search:
        fields = ("title", "description", "claim_text", "sources") if table == "claims" else ("myth_title", "myth_description", "debunked_explanation", "scientific_evidence", "sources")
        conditions.append("(" + " OR ".join(f"{field} LIKE ?" for field in fields) + ")")
        values.extend([f"%{search}%"] * len(fields))
    where = " WHERE " + " AND ".join(conditions) if conditions else ""
    with closing(get_db_connection()) as conn:
        rows = conn.execute(f"SELECT * FROM {table}{where} ORDER BY created_at DESC", values).fetchall()
    records = [dict(row) for row in rows]
    for record in records:
        record["sources"] = parse_sources(record.get("sources"))
    return records


def error(message, code):
    return jsonify({"status": "error", "message": message}), code


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/health")
def health_check():
    return jsonify({"status": "healthy"})


@app.get("/api/claims")
def get_claims():
    status = request.args.get("status")
    if status and status not in VALID_STATUSES:
        return error("Unsupported verification status", 400)
    data = list_records("claims", status, request.args.get("category"), clean_text(request.args.get("q", ""), 200))
    return jsonify({"status": "success", "data": data, "count": len(data)})


@app.get("/api/claims/<int:claim_id>")
def get_claim(claim_id):
    rows = list_records("claims")
    item = next((row for row in rows if row["id"] == claim_id), None)
    return (jsonify({"status": "success", "data": item}), 200) if item else error("Claim not found", 404)


@app.post("/api/claims")
def create_claim():
    data = request.get_json(silent=True) or {}
    title, text = clean_text(data.get("title"), 180), clean_text(data.get("claim_text"))
    status = clean_text(data.get("verification_status", "pending"), 30).lower()
    category = clean_text(data.get("category", "other"), 40).lower()
    if not title or not text:
        return error("Title and claim text are required", 400)
    if status not in VALID_STATUSES:
        return error("Unsupported verification status", 400)
    if category not in VALID_CATEGORIES:
        return error("Unsupported scientific topic", 400)
    with closing(get_db_connection()) as conn:
        cursor = conn.execute("INSERT INTO claims (title, description, claim_text, verification_status, sources, author, category) VALUES (?, ?, ?, ?, ?, ?, ?)", (title, clean_text(data.get("description")), text, status, json.dumps(parse_sources(data.get("sources"))), clean_text(data.get("author"), 100) or "Anonymous", category))
        conn.commit()
        record_id = cursor.lastrowid
    return jsonify({"status": "success", "message": "Claim submitted for review", "id": record_id}), 201


@app.get("/api/myths")
def get_myths():
    data = list_records("myths", category=request.args.get("category"), search=clean_text(request.args.get("q", ""), 200))
    return jsonify({"status": "success", "data": data, "count": len(data)})


@app.get("/api/myths/<int:myth_id>")
def get_myth(myth_id):
    rows = list_records("myths")
    item = next((row for row in rows if row["id"] == myth_id), None)
    return (jsonify({"status": "success", "data": item}), 200) if item else error("Myth not found", 404)


@app.post("/api/myths")
def create_myth():
    data = request.get_json(silent=True) or {}
    title = clean_text(data.get("myth_title"), 180)
    explanation = clean_text(data.get("debunked_explanation"))
    evidence = clean_text(data.get("scientific_evidence"))
    category = clean_text(data.get("category", "other"), 40).lower()
    if not title or not explanation or not evidence:
        return error("Myth title, explanation, and scientific evidence are required", 400)
    if category not in VALID_CATEGORIES:
        return error("Unsupported scientific topic", 400)
    with closing(get_db_connection()) as conn:
        cursor = conn.execute("INSERT INTO myths (myth_title, myth_description, debunked_explanation, scientific_evidence, sources, author, category) VALUES (?, ?, ?, ?, ?, ?, ?)", (title, clean_text(data.get("myth_description")), explanation, evidence, json.dumps(parse_sources(data.get("sources"))), clean_text(data.get("author"), 100) or "Anonymous", category))
        conn.commit()
        record_id = cursor.lastrowid
    return jsonify({"status": "success", "message": "Evidence note submitted", "id": record_id}), 201


@app.post("/api/claims/<int:claim_id>/engage")
def engage_claim(claim_id):
    with closing(get_db_connection()) as conn:
        cursor = conn.execute("UPDATE claims SET engagement = engagement + 1 WHERE id = ?", (claim_id,))
        conn.commit()
        if cursor.rowcount == 0:
            return error("Claim not found", 404)
        count = conn.execute("SELECT engagement FROM claims WHERE id = ?", (claim_id,)).fetchone()[0]
    return jsonify({"status": "success", "engagement": count})


@app.post("/api/myths/<int:myth_id>/engage")
def engage_myth(myth_id):
    with closing(get_db_connection()) as conn:
        cursor = conn.execute("UPDATE myths SET engagement = engagement + 1 WHERE id = ?", (myth_id,))
        conn.commit()
        if cursor.rowcount == 0:
            return error("Myth not found", 404)
        count = conn.execute("SELECT engagement FROM myths WHERE id = ?", (myth_id,)).fetchone()[0]
    return jsonify({"status": "success", "engagement": count})


@app.post("/api/ai/analyze")
def analyze_claim():
    data = request.get_json(silent=True) or {}
    text = clean_text(data.get("claim_text"))
    if not text:
        return error("Claim text is required", 400)
    sources = parse_sources(data.get("sources"))
    return jsonify({"status": "success", "data": {
        "summary": "This tool does not independently verify scientific claims. Use the checklist below to evaluate the evidence.",
        "key_points": ["Identify the precise, testable statement and relevant scientific field.", "Check whether cited work is peer-reviewed and directly supports the statement.", "Compare results with systematic reviews, replication studies, and expert consensus.", "Consider uncertainty, limitations, conflicts of interest, and competing explanations."],
        "questions_to_ask": ["Can the cited source be independently accessed?", "Does the study measure the outcome claimed?", "Have independent teams replicated the result?", "What evidence would change this conclusion?"],
        "sources_provided": sources,
        "confidence": "No verdict assigned — a source-backed human review is needed."
    }})


@app.get("/api/quiz/generate/<int:claim_id>")
def generate_claim_quiz(claim_id):
    with closing(get_db_connection()) as conn:
        claim = conn.execute("SELECT title, claim_text, verification_status FROM claims WHERE id = ?", (claim_id,)).fetchone()
    if claim is None:
        return error("Claim not found", 404)
    return jsonify({"status": "success", "claim_id": claim_id, "data": {
        "question": f"What evidence would support or challenge this claim: {claim['claim_text']}",
        "answer": f"Current community status: {claim['verification_status']}. Review the cited sources and study methods; this status is not an independent scientific verdict."
    }})


@app.get("/api/quiz/generate/myth/<int:myth_id>")
def generate_myth_quiz(myth_id):
    with closing(get_db_connection()) as conn:
        myth = conn.execute("SELECT myth_title, debunked_explanation, scientific_evidence FROM myths WHERE id = ?", (myth_id,)).fetchone()
    if myth is None:
        return error("Myth not found", 404)
    return jsonify({"status": "success", "myth_id": myth_id, "data": {
        "question": f"What evidence is presented about this statement: {myth['myth_title']}?",
        "answer": f"Submitted explanation: {myth['debunked_explanation']} Evidence note: {myth['scientific_evidence']}"
    }})


@app.post("/api/ai/ask")
def ask_evidence_question():
    data = request.get_json(silent=True) or {}
    query = clean_text(data.get("query"), 2000)
    if not query:
        return error("Query is required", 400)
    return jsonify({"status": "success", "data": {
        "response": "Cosmos does not make automated truth judgments. Evaluate the original sources, methods, replication, and uncertainty before reaching a conclusion.",
        "type": "review_required",
        "context": clean_text(data.get("context") or data.get("claim_text"), 2000),
        "ai_note": "This is a general evidence-review reminder, not a literature search or scientific assessment."
    }})


@app.errorhandler(404)
def not_found(_error):
    return error("Endpoint not found", 404)


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
