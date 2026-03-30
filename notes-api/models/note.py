class Note:
    def __init__(self, title: str, content: str):
        self.title = title
        self.content = content
        self.undo_stack: list[str] = []
        self.redo_stack: list[str] = []

    def change_content(self, new_content: str):
        self.undo_stack.append(self.content)
        self.content = new_content
        self.redo_stack.clear()

    def undo(self) -> dict:
        if not self.undo_stack:
            return {"success": False, "message": "Nothing to undo"}
        self.redo_stack.append(self.content)
        self.content = self.undo_stack.pop()
        return {"success": True, "content": self.content}

    def redo(self) -> dict:
        if not self.redo_stack:
            return {"success": False, "message": "Nothing to redo"}
        self.undo_stack.append(self.content)
        self.content = self.redo_stack.pop()
        return {"success": True, "content": self.content}

    def matches_query(self, query: str) -> bool:
        query = query.lower().strip()
        content_lower = self.content.lower()
        words = content_lower.split()
        # Check each word for partial or full match
        # Note: using split() fixes the C++ bug where the last word was skipped
        for word in words:
            if query in word:
                return True
        return False

    def to_dict(self) -> dict:
        return {"title": self.title, "content": self.content}
