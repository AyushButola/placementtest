import React, { useState, useEffect } from 'react';
import './App.css';
import Sidebar from './components/Sidebar';
import NoteEditor from './components/NoteEditor';

const API_BASE_URL = 'http://127.0.0.1:5000/notes';

function App() {
  const [notes, setNotes] = useState([]);
  const [selectedNoteTitle, setSelectedNoteTitle] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');

  const fetchNotes = async () => {
    try {
      const response = await fetch(API_BASE_URL);
      const data = await response.json();
      setNotes(data);
    } catch (error) {
      console.error('Error fetching notes:', error);
    }
  };

  const performSearch = async (query) => {
    if (!query) {
      fetchNotes();
      return;
    }
    try {
      const response = await fetch(`${API_BASE_URL}/search/content?query=${encodeURIComponent(query)}`);
      const data = await response.json();
      // data.results is array of titles
      const matchedTitles = data.results;
      // Fetch full notes and filter locally based on the returned titles from backend
      const res = await fetch(API_BASE_URL);
      const allNotes = await res.json();
      setNotes(allNotes.filter(n => matchedTitles.includes(n.title)));
    } catch (error) {
      console.error('Error searching notes:', error);
    }
  };

  useEffect(() => {
    fetchNotes();
  }, []);

  useEffect(() => {
    const delayDebounceOptions = setTimeout(() => {
      performSearch(searchQuery);
    }, 300);
    return () => clearTimeout(delayDebounceOptions);
  }, [searchQuery]);

  const handleCreateNote = async (title, content) => {
    try {
      const res = await fetch(API_BASE_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, content })
      });
      if (res.ok) {
        await fetchNotes();
        setSelectedNoteTitle(title);
      } else {
        const errorData = await res.json();
        alert(`Error: ${errorData.error}`);
      }
    } catch (error) {
      console.error('Error creating note:', error);
    }
  };

  const handleUpdateNote = async (title, newContent) => {
    try {
      await fetch(`${API_BASE_URL}/${title}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: newContent })
      });
      fetchNotes();
      // We don't change selection
    } catch (error) {
      console.error('Error updating note:', error);
    }
  };

  const handleUndo = async (title) => {
    try {
      const res = await fetch(`${API_BASE_URL}/${title}/undo`, { method: 'POST' });
      if (res.ok) {
        fetchNotes();
      } else {
        const data = await res.json();
        alert(data.error || "Cannot undo");
      }
    } catch (error) {
      console.error('Error undoing:', error);
    }
  };

  const handleRedo = async (title) => {
    try {
      const res = await fetch(`${API_BASE_URL}/${title}/redo`, { method: 'POST' });
      if (res.ok) {
        fetchNotes();
      } else {
        const data = await res.json();
        alert(data.error || "Cannot redo");
      }
    } catch (error) {
      console.error('Error redoing:', error);
    }
  };

  const selectedNote = notes.find(n => n.title === selectedNoteTitle);

  return (
    <div className="app-container">
      <Sidebar 
        notes={notes} 
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        selectedNoteTitle={selectedNoteTitle}
        onSelectNote={setSelectedNoteTitle}
        onCreateNote={handleCreateNote}
      />
      <NoteEditor 
        note={selectedNote} 
        onUpdate={handleUpdateNote}
        onUndo={handleUndo}
        onRedo={handleRedo}
      />
    </div>
  );
}

export default App;
