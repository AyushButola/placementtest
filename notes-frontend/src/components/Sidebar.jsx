import React, { useState } from 'react';

function Sidebar({ notes, searchQuery, setSearchQuery, selectedNoteTitle, onSelectNote, onCreateNote }) {
  const [newTitle, setNewTitle] = useState('');
  const [newContent, setNewContent] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  const handleCreate = (e) => {
    e.preventDefault();
    if(newTitle.trim() && newContent.trim()) {
      onCreateNote(newTitle, newContent);
      setNewTitle('');
      setNewContent('');
      setIsCreating(false);
    }
  };

  return (
    <div className="sidebar">
      <div className="brand-title">Notes App</div>
      
      <div className="search-container">
        <input 
          type="text" 
          placeholder="Search partial content..." 
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      {!isCreating ? (
        <button className="btn btn-primary" onClick={() => setIsCreating(true)}>
          + New Note
        </button>
      ) : (
        <form onSubmit={handleCreate} className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1rem' }}>
          <input 
            type="text" 
            placeholder="Note Title" 
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            style={{ padding: '0.8rem', borderRadius: '8px', border: 'none', background: 'rgba(255,255,255,0.8)' }}
            required
          />
          <input 
            type="text" 
            placeholder="Initial Content" 
            value={newContent}
            onChange={(e) => setNewContent(e.target.value)}
            style={{ padding: '0.8rem', borderRadius: '8px', border: 'none', background: 'rgba(255,255,255,0.8)' }}
            required
          />
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button type="submit" className="btn btn-primary" style={{ margin: 0, padding: '0.8rem', flex: 1 }}>Add</button>
            <button type="button" className="btn btn-secondary" style={{ padding: '0.8rem', flex: 1 }} onClick={() => setIsCreating(false)}>Cancel</button>
          </div>
        </form>
      )}

      <div className="note-list">
        {notes.length === 0 ? (
          <div style={{ color: 'var(--text-muted)' }}>No notes found.</div>
        ) : (
          notes.map(note => (
            <div 
              key={note.title} 
              className={`note-item ${selectedNoteTitle === note.title ? 'active' : ''}`}
              onClick={() => onSelectNote(note.title)}
            >
              <div className="note-item-title">{note.title}</div>
              <div className="note-item-preview">{note.content}</div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default Sidebar;
