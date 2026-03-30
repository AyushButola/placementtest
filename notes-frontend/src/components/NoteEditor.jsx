import React, { useState, useEffect } from 'react';

function NoteEditor({ note, onUpdate, onUndo, onRedo }) {
  const [content, setContent] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (note) {
      setContent(note.content);
    }
  }, [note]);

  // Debounce the update call so we save after user stops typing
  useEffect(() => {
    if(!note) return;
    
    // Only update if content changed from prop
    if(content === note.content) return;

    const handler = setTimeout(() => {
      onUpdate(note.title, content);
      setIsSaving(true);
      setTimeout(() => setIsSaving(false), 1000); // hide indicator after 1s
    }, 1000);

    return () => clearTimeout(handler);
  }, [content, note]);

  if (!note) {
    return (
      <div className="editor-container">
        <div className="editor-empty">
          <p>Select a note or create a new one to begin editing.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="editor-container animate-fade-in">
      <div className={`save-indicator ${isSaving ? 'visible' : ''}`}>
        Auto-saved
      </div>
      
      <div className="editor-header">
        <input 
          type="text" 
          className="editor-title" 
          value={note.title} 
          readOnly 
        />
        <div className="editor-toolbar">
          <button className="btn btn-secondary" onClick={() => onUndo(note.title)}>Undo</button>
          <button className="btn btn-secondary" onClick={() => onRedo(note.title)}>Redo</button>
        </div>
      </div>
      
      <textarea 
        className="editor-textarea"
        value={content}
        onChange={(e) => setContent(e.target.value)}
        placeholder="Start typing your note here..."
      />
    </div>
  );
}

export default NoteEditor;
