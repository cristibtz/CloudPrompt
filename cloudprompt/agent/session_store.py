from __future__ import annotations

from typing import Optional, Dict


class InMemorySessionStore:
    """Simple in-memory store for session-scoped data.

    Replace with a Redis/DB-backed store in production. API is intentionally minimal
    and cloud-agnostic so it can hold tokens/flags for AWS/Azure/GCP/Proxmox, etc.
    """

    def __init__(self) -> None:
        self._store: Dict[str, Dict[str, str]] = {}

    def load(self, session_id: Optional[str]) -> Dict[str, str]:
        if not session_id:
            return {}
        return self._store.get(session_id, {}).copy()

    def save(self, session_id: Optional[str], kv: Dict[str, str]) -> None:
        if not session_id:
            return
        existing = self._store.get(session_id, {})
        existing.update({k: v for k, v in kv.items() if v})
        self._store[session_id] = existing
