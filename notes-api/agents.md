# Agent Instructions — Migrate Notes API from In-Memory to SQLite

You are modifying an **existing** Flask Notes API to replace in-memory storage with a persistent SQLite database using `flask-sqlalchemy`.

The existing project is already working. Your job is to **modify** it — not rewrite it from scratch.  
Follow every step in order. Do not change any route URLs, HTTP methods, or response shapes.

---

## What Is Changing and Why

| Was | Now |
|---|---|
| `notes_store: dict` — wiped on restart | SQLite file `notes.db` — persists forever |
| `Note` Python class with list-based undo/redo stacks | `Note` SQLAlchemy model + `NoteHistory` table for undo/redo |
| Undo/redo via `list.append` / `list.pop` | Undo/redo via version pointer on history rows |

The API surface (URLs, methods, request/response JSON) stays **100% identical**.

---

## Updated Project Structure

Add one new file. Modify three existing files.

```
notes-api/
├── app.py                  ← MODIFY
├── database.py             ← CREATE (new)
├── models/
│   ├── __init__.py
│   └── note.py             ← REPLACE ENTIRELY
├── routes/
│   ├── __init__.py
│   └── notes.py            ← MODIFY
└── requirements.txt        ← MODIFY
```

---

## Step 1 — Update `requirements.txt`

```
flask
flask-sqlalchemy
flask-cors
```

Install:
```bash
pip install flask flask-sqlalchemy flask-cors
```

---

## Step 2 — Create `database.py`

This file creates the single shared `db` instance used across the whole app.  
Every other file imports `db` from here — never create a second `SQLAlchemy()` instance.

```python
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
```

---

## Step 3 — Replace `models/note.py` entirely

This replaces the old in-memory `Note` class with two SQLAlchemy models:
- `Note` — stores title and current content
- `NoteHistory` — stores every past version of a note's content, with a version number

The undo/redo logic is now implemented by moving the `current_version` pointer on the `Note` row.

```python
from database import db


class Note(db.Model):
    __tablename__ = "notes"

    title = db.Column(db.String, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    current_version = db.Column(db.Integer, default=0)

    history = db.relationship(
        "NoteHistory",
        backref="note",
        cascade="all, delete-orphan",
        order_by="NoteHistory.version"
    )

    def change_content(self, new_content: str):
        # Delete all history rows with version > current_version (clears redo)
        NoteHistory.query.filter(
            NoteHistory.note_title == self.title,
            NoteHistory.version > self.current_version
        ).delete()

        # Increment version and save new history row
        self.current_version += 1
        history_entry = NoteHistory(
            note_title=self.title,
            content=new_content,
            version=self.current_version
        )
        db.session.add(history_entry)
        self.content = new_content

    def undo(self) -> dict:
        if self.current_version <= 1:
            return {"success": False, "message": "Nothing to undo"}

        self.current_version -= 1
        target = NoteHistory.query.filter_by(
            note_title=self.title,
            version=self.current_version
        ).first()
        self.content = target.content
        return {"success": True, "content": self.content}

    def redo(self) -> dict:
        max_version = db.session.query(
            db.func.max(NoteHistory.version)
        ).filter_by(note_title=self.title).scalar()

        if max_version is None or self.current_version >= max_version:
            return {"success": False, "message": "Nothing to redo"}

        self.current_version += 1
        target = NoteHistory.query.filter_by(
            note_title=self.title,
            version=self.current_version
        ).first()
        self.content = target.content
        return {"success": True, "content": self.content}

    def matches_query(self, query: str) -> bool:
        query = query.lower().strip()
        words = self.content.lower().split()
        for word in words:
            if query in word:
                return True
        return False

    def to_dict(self) -> dict:
        return {"title": self.title, "content": self.content}


class NoteHistory(db.Model):
    __tablename__ = "note_history"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    note_title = db.Column(db.String, db.ForeignKey("notes.title"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    version = db.Column(db.Integer, nullable=False)
```

**How undo/redo works with versions:**

```
Action               notes.current_version    note_history rows
-----------------------------------------------------------------
Create note          1                        [v1: "original"]
Edit → "second"      2                        [v1, v2: "second"]
Edit → "third"       3                        [v1, v2, v3: "third"]
Undo                 2                        [v1, v2, v3]  ← pointer moves back
Undo                 1                        [v1, v2, v3]  ← pointer moves back
Redo                 2                        [v1, v2, v3]  ← pointer moves forward
Edit → "new"         3                        [v1, v2, v3: "new"]  ← v3 replaced (old redo gone)
```

---

## Step 4 — Replace `routes/notes.py` entirely

The route logic is almost identical to the original — the only difference is replacing `notes_store` dict operations with SQLAlchemy queries. All URLs, methods, and response shapes are unchanged.

```python
from flask import Blueprint, request, jsonify
from database import db
from models.note import Note, NoteHistory

notes_bp = Blueprint("notes", __name__)


# ---------------------------------------------------------------
# POST /notes — Create a new note
# ---------------------------------------------------------------
@notes_bp.route("/notes", methods=["POST"])
def create_note():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    title = data.get("title", "").strip()
    content = data.get("content", "").strip()

    if not title:
        return jsonify({"error": "Title cannot be empty"}), 400
    if not content:
        return jsonify({"error": "Content cannot be empty"}), 400

    if Note.query.get(title):
        return jsonify({"error": f"Note with title '{title}' already exists"}), 409

    note = Note(title=title, content=content, current_version=1)
    db.session.add(note)

    # Save initial version to history
    history_entry = NoteHistory(note_title=title, content=content, version=1)
    db.session.add(history_entry)

    db.session.commit()
    return jsonify({"message": "Note created", "title": title}), 201


# ---------------------------------------------------------------
# GET /notes — Get all notes
# ---------------------------------------------------------------
@notes_bp.route("/notes", methods=["GET"])
def get_all_notes():
    notes = Note.query.all()
    return jsonify([note.to_dict() for note in notes]), 200


# ---------------------------------------------------------------
# GET /notes/search/content?query=<query>
# IMPORTANT: Must be defined BEFORE GET /notes/<title>
# ---------------------------------------------------------------
@notes_bp.route("/notes/search/content", methods=["GET"])
def search_notes():
    query = request.args.get("query", "").strip()

    if not query:
        return jsonify({"error": "Query parameter cannot be empty"}), 400

    matched_titles = [
        note.title
        for note in Note.query.all()
        if note.matches_query(query)
    ]
    return jsonify({"query": query, "results": matched_titles}), 200


# ---------------------------------------------------------------
# GET /notes/<title> — Get a specific note
# ---------------------------------------------------------------
@notes_bp.route("/notes/<string:title>", methods=["GET"])
def get_note(title):
    note = Note.query.get(title)
    if not note:
        return jsonify({"error": f"Note '{title}' not found"}), 404
    return jsonify(note.to_dict()), 200


# ---------------------------------------------------------------
# PUT /notes/<title> — Edit a note's content
# ---------------------------------------------------------------
@notes_bp.route("/notes/<string:title>", methods=["PUT"])
def update_note(title):
    note = Note.query.get(title)
    if not note:
        return jsonify({"error": f"Note '{title}' not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    new_content = data.get("content", "").strip()
    if not new_content:
        return jsonify({"error": "Content cannot be empty"}), 400

    note.change_content(new_content)
    db.session.commit()
    return jsonify({"message": "Note updated", "title": title}), 200


# ---------------------------------------------------------------
# POST /notes/<title>/undo
# ---------------------------------------------------------------
@notes_bp.route("/notes/<string:title>/undo", methods=["POST"])
def undo_note(title):
    note = Note.query.get(title)
    if not note:
        return jsonify({"error": f"Note '{title}' not found"}), 404

    result = note.undo()
    if not result["success"]:
        return jsonify({"error": result["message"]}), 400

    db.session.commit()
    return jsonify({"message": "Undo successful", "content": result["content"]}), 200


# ---------------------------------------------------------------
# POST /notes/<title>/redo
# ---------------------------------------------------------------
@notes_bp.route("/notes/<string:title>/redo", methods=["POST"])
def redo_note(title):
    note = Note.query.get(title)
    if not note:
        return jsonify({"error": f"Note '{title}' not found"}), 404

    result = note.redo()
    if not result["success"]:
        return jsonify({"error": result["message"]}), 400

    db.session.commit()
    return jsonify({"message": "Redo successful", "content": result["content"]}), 200
```

---

## Step 5 — Update `app.py`

```python
from flask import Flask
from flask_cors import CORS
from database import db
from routes.notes import notes_bp


def create_app():
    app = Flask(__name__)

    # SQLite config — creates notes.db in the project root
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///notes.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    CORS(app)
    db.init_app(app)

    app.register_blueprint(notes_bp)

    # Create tables on first run if they don't exist
    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
```

---

## Step 6 — Delete the old `notes.db` if it exists

If the server was run before this migration, there may be a stale `notes.db` with the wrong schema. Delete it and let `db.create_all()` recreate it cleanly:

```bash
rm -f notes-api/notes.db
```

Then start the server:

```bash
python app.py
```

---

## Step 7 — Verify with curl

These are identical to the original curl commands — the API surface has not changed.

**Create a note:**
```bash
curl -X POST http://127.0.0.1:5000/notes \
  -H "Content-Type: application/json" \
  -d '{"title": "Shopping", "content": "Buy apples oranges and milk"}'
```

**Edit it:**
```bash
curl -X PUT http://127.0.0.1:5000/notes/Shopping \
  -H "Content-Type: application/json" \
  -d '{"content": "Buy apples oranges milk and bread"}'
```

**Undo:**
```bash
curl -X POST http://127.0.0.1:5000/notes/Shopping/undo
```

**Redo:**
```bash
curl -X POST http://127.0.0.1:5000/notes/Shopping/redo
```

**Restart the server and confirm notes survived:**
```bash
# Stop the server (Ctrl+C), restart it, then:
curl http://127.0.0.1:5000/notes
# Notes must still be there — this confirms SQLite persistence is working
```

---

## Critical Rules — Do Not Violate

1. **Never create a second `SQLAlchemy()` instance** — only `database.py` creates `db = SQLAlchemy()`. All other files import from `database`.

2. **Always call `db.session.commit()`** after any write operation (create, update, undo, redo) — without it, changes are rolled back when the request ends.

3. **`db.create_all()` must run inside `app.app_context()`** — SQLAlchemy needs the app context to know which database to talk to.

4. **Route order still matters** — `GET /notes/search/content` must remain above `GET /notes/<title>` in `routes/notes.py`.

5. **Do not change any URL, HTTP method, or JSON response shape** — the frontend depends on the existing API contract.

6. **`change_content` must delete history rows with version > current_version** — this is what clears the redo history on a new edit, equivalent to `redo_stack.clear()` in the old code.

7. **`notes.db` is created automatically** — do not create it manually, do not commit it to version control, add it to `.gitignore`.