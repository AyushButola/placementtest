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
