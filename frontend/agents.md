# Agent Instructions — Notes App Frontend (HTML + CSS + JS)

You are building a single-page frontend for a notes-taking app.  
The backend is already running at `http://127.0.0.1:5000`.  
All API details are defined below — do not deviate from them.

---

## Deliverable

One file: `index.html`  
It must contain all HTML, CSS, and JavaScript inline — no separate files, no build tools, no frameworks, no npm.

---

## Backend API Reference

Base URL: `http://127.0.0.1:5000`

| Action | Method | URL | Body / Params |
|---|---|---|---|
| Create note | POST | `/notes` | JSON: `{ title, content }` |
| Get all notes | GET | `/notes` | — |
| Get one note | GET | `/notes/<title>` | — |
| Edit note | PUT | `/notes/<title>` | JSON: `{ content }` |
| Undo last edit | POST | `/notes/<title>/undo` | — |
| Redo last edit | POST | `/notes/<title>/redo` | — |
| Search content | GET | `/notes/search/content?query=<q>` | query param |

All request bodies are JSON. All responses are JSON.  
Errors come back as `{ "error": "..." }`.  
Success responses include `message`, `title`, `content`, or `results` depending on the endpoint.

---

## UI Sections to Build

Build the page as **three panels** laid out side by side on desktop, stacked on mobile:

### Panel 1 — Sidebar: Note List + Search
- A search input at the top (calls `GET /notes/search/content?query=...` on every keystroke with debounce of 300ms)
- When search input is empty, show all notes fetched from `GET /notes`
- List of note titles — clicking a title loads that note into Panel 2
- A **"+ New Note"** button that clears Panel 2 and shows the create form

### Panel 2 — Main: View / Edit / Create
This panel has two states:

**View/Edit state** (when a note is selected from the sidebar):
- Display the note title at the top (not editable)
- A textarea showing the note content (editable)
- A **"Save"** button → calls `PUT /notes/<title>` with the new content
- An **"Undo"** button → calls `POST /notes/<title>/undo`, then refreshes content
- A **"Redo"** button → calls `POST /notes/<title>/redo`, then refreshes content
- After undo/redo, update the textarea with the returned `content`

**Create state** (when "+ New Note" is clicked):
- An input field for title
- A textarea for content
- A **"Create"** button → calls `POST /notes` with `{ title, content }`
- On success, reload the note list and switch to View/Edit state for the new note

### Panel 3 — Info Bar
- Shows metadata about the currently selected note:
  - Title
  - Character count of content (updates live as user types in the textarea)
  - Word count (same)
- If no note is selected, show a placeholder message

---

## JavaScript — Exact Functions to Implement

Implement each function with this exact name and behaviour:

**`fetchAllNotes()`**
- `GET /notes`
- Renders the list of note titles in the sidebar
- Each title is a clickable element that calls `loadNote(title)`

**`loadNote(title)`**
- `GET /notes/<title>`
- Populates Panel 2 in View/Edit state
- Updates Panel 3 with title, char count, word count
- Stores `currentTitle` in a module-level variable

**`saveNote()`**
- Reads content from the textarea
- `PUT /notes/<currentTitle>` with `{ content }`
- Shows inline success or error feedback next to the Save button

**`undoNote()`**
- `POST /notes/<currentTitle>/undo`
- On success: update textarea with `response.content`
- On 400: show inline error "Nothing to undo"

**`redoNote()`**
- `POST /notes/<currentTitle>/redo`
- On success: update textarea with `response.content`
- On 400: show inline error "Nothing to redo"

**`createNote()`**
- Reads title and content from the create form inputs
- `POST /notes` with `{ title, content }`
- On 201: call `fetchAllNotes()` then `loadNote(newTitle)`
- On 409: show inline error "A note with this title already exists"
- On 400: show inline error with the server's error message

**`searchNotes(query)`**
- `GET /notes/search/content?query=<query>`
- Renders only the matched titles in the sidebar
- If query is empty string, call `fetchAllNotes()` instead

**`updateInfoBar()`**
- Reads current textarea value
- Updates char count and word count in Panel 3 live

---

## Error Handling Rules

- Every `fetch` call must be wrapped in `try/catch`
- Network errors → show a dismissible banner at the top: `"Could not reach the server. Is it running?"`
- API errors (`response.ok === false`) → read `response.json()` and show the `error` field inline near the relevant action
- Never use `alert()` or `console.log()` for user-facing feedback — all feedback must be inline in the UI

---

## CORS Note

The Flask backend must have CORS enabled. If fetch calls fail with a CORS error, add this to `app.py` before running:

```python
pip install flask-cors
```

```python
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)
    app.register_blueprint(notes_bp)
    return app
```

---

## Design & Aesthetic Direction

- Use a clean **dark theme** — dark backgrounds (`#0f0f0f`, `#1a1a1a`), off-white text (`#e8e8e8`), with a warm amber accent (`#f5a623`) for buttons and active states
- Import **"IBM Plex Mono"** from Google Fonts for all text — this gives it a focused, utilitarian "developer notebook" feel
- Sidebar note titles should have a subtle left border that turns amber when active
- Buttons should be minimal — outlined style, no heavy fills, accent color on hover
- Textarea should have no visible border in resting state, only a subtle bottom line; expands to fill available height
- Transitions on all interactive elements: `transition: all 0.15s ease`
- Panel borders: `1px solid #2a2a2a`
- No box shadows — use borders only for separation
- Mobile: stack panels vertically, hide Panel 3 below Panel 2

---

## Critical Rules — Do Not Violate

1. **Single file only** — all CSS in a `<style>` tag, all JS in a `<script>` tag, inside one `index.html`
2. **No frameworks** — no React, Vue, jQuery, Bootstrap, Tailwind, etc.
3. **No `async` libraries** — use native `fetch` with `async/await`
4. **Search must debounce** — do not fire a request on every single keypress; wait 300ms after the user stops typing
5. **`currentTitle` must be module-scoped** — declare it at the top of the script block as `let currentTitle = null;`
6. **After every create/save/undo/redo** — always refresh the displayed content from the server response; do not assume the UI state is correct
7. **Search route must use query param** — `?query=value`, not a path param
8. **Do not hardcode any note titles** — everything is dynamic from API responses
9. **CORS** — remind the user to enable flask-cors if requests fail (see CORS Note section above)