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
