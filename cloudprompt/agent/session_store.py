from __future__ import annotations

from typing import Optional, Dict
import time
import json
import os
from pathlib import Path
from rich.console import Console

console = Console()


class InMemorySessionStore:
    """Session store with file-based persistence for CLI usage.

    Stores session data in ~/.cloudprompt/sessions/ for persistence across CLI calls.
    Falls back to in-memory storage if file operations fail.
    """

    def __init__(self) -> None:
        self._store: Dict[str, Dict[str, str]] = {}
        self._timestamps: Dict[str, float] = {}
        
        # Set up persistent storage directory
        self._storage_dir = Path.home() / ".cloudprompt" / "sessions"
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing sessions from disk
        self._load_from_disk()

    def _get_session_file(self, session_id: str) -> Path:
        """Get the file path for a session"""
        safe_session_id = "".join(c for c in session_id if c.isalnum() or c in "-_.")
        return self._storage_dir / f"{safe_session_id}.json"

    def _load_from_disk(self):
        """Load all sessions from disk into memory"""
        try:
            for session_file in self._storage_dir.glob("*.json"):
                session_id = session_file.stem
                try:
                    with open(session_file, 'r') as f:
                        data = json.load(f)
                        if 'tokens' in data and 'timestamp' in data:
                            self._store[session_id] = data['tokens']
                            self._timestamps[session_id] = data['timestamp']
                except (json.JSONDecodeError, KeyError, OSError):
                    # Skip corrupted files
                    continue
        except OSError:
            # Directory doesn't exist or can't be read, use in-memory only
            pass

    def _save_to_disk(self, session_id: str):
        """Save a session to disk"""
        try:
            session_file = self._get_session_file(session_id)
            data = {
                'tokens': self._store.get(session_id, {}),
                'timestamp': self._timestamps.get(session_id, time.time())
            }
            with open(session_file, 'w') as f:
                json.dump(data, f, indent=2)
        except OSError:
            # Can't write to disk, continue with in-memory only
            console.print(f"[yellow]⚠️ Could not persist session '{session_id}' to disk[/yellow]")

    def load(self, session_id: Optional[str]) -> Dict[str, str]:
        if not session_id:
            return {}
        
        # Try to load from disk if not in memory
        if session_id not in self._store:
            try:
                session_file = self._get_session_file(session_id)
                if session_file.exists():
                    with open(session_file, 'r') as f:
                        data = json.load(f)
                        if 'tokens' in data and 'timestamp' in data:
                            self._store[session_id] = data['tokens']
                            self._timestamps[session_id] = data['timestamp']
            except (json.JSONDecodeError, KeyError, OSError):
                pass
        
        data = self._store.get(session_id, {}).copy()
        timestamp = self._timestamps.get(session_id)
        
        if data:
            age_minutes = (time.time() - timestamp) / 60 if timestamp else 0
            console.print(f"[cyan]📥 Loaded session '{session_id}': {list(data.keys())} (age: {age_minutes:.1f}min)[/cyan]")
        
        return data

    def save(self, session_id: Optional[str], kv: Dict[str, str]) -> None:
        if not session_id:
            return
        
        # Only save non-empty values
        filtered_kv = {k: v for k, v in kv.items() if v}
        if not filtered_kv:
            return
        
        existing = self._store.get(session_id, {})
        existing.update(filtered_kv)
        self._store[session_id] = existing
        self._timestamps[session_id] = time.time()
        
        # Persist to disk
        self._save_to_disk(session_id)
        
        console.print(f"[cyan]💾 Saved to session '{session_id}': {list(filtered_kv.keys())}[/cyan]")

    def clear_session(self, session_id: Optional[str]) -> None:
        """Clear all data for a specific session"""
        if session_id:
            # Remove from memory
            if session_id in self._store:
                del self._store[session_id]
            if session_id in self._timestamps:
                del self._timestamps[session_id]
            
            # Remove from disk
            try:
                session_file = self._get_session_file(session_id)
                if session_file.exists():
                    session_file.unlink()
            except OSError:
                pass
            
            console.print(f"[yellow]🗑️ Cleared session '{session_id}'[/yellow]")

    def list_sessions(self) -> Dict[str, Dict[str, str]]:
        """List all active sessions (for debugging)"""
        return {k: v.copy() for k, v in self._store.items()}
