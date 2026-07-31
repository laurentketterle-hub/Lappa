"""Collaborative workspace presence — lightweight multi-user tracking (mock OK)."""

import json
import time
import uuid
import logging
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class UserPresence:
    """User presence in a workspace."""
    user_id: str
    username: str
    cursor_line: int = 0
    cursor_col: int = 0
    active_file: str = ""
    last_seen: float = field(default_factory=time.time)
    color: str = "#4FC3F7"
    
    @property
    def is_active(self) -> bool:
        return (time.time() - self.last_seen) < 30  # 30s timeout


@dataclass
class WorkspaceState:
    """State of a collaborative workspace."""
    workspace_id: str
    name: str
    users: Dict[str, UserPresence] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    
    def add_user(self, user_id: str, username: str, color: str = None) -> UserPresence:
        presence = UserPresence(
            user_id=user_id,
            username=username,
            color=color or _generate_color(user_id)
        )
        self.users[user_id] = presence
        return presence
    
    def remove_user(self, user_id: str) -> bool:
        if user_id in self.users:
            del self.users[user_id]
            return True
        return False
    
    def get_active_users(self) -> List[UserPresence]:
        return [u for u in self.users.values() if u.is_active]
    
    def update_cursor(self, user_id: str, line: int, col: int, file_path: str = ""):
        if user_id in self.users:
            self.users[user_id].cursor_line = line
            self.users[user_id].cursor_col = col
            self.users[user_id].last_seen = time.time()
            if file_path:
                self.users[user_id].active_file = file_path


class PresenceService:
    """In-memory presence service — mock for CI."""
    
    def __init__(self):
        self._workspaces: Dict[str, WorkspaceState] = {}
    
    def create_workspace(self, name: str, workspace_id: str = None) -> WorkspaceState:
        ws_id = workspace_id or str(uuid.uuid4())
        ws = WorkspaceState(workspace_id=ws_id, name=name)
        self._workspaces[ws_id] = ws
        return ws
    
    def get_workspace(self, workspace_id: str) -> Optional[WorkspaceState]:
        return self._workspaces.get(workspace_id)
    
    def list_workspaces(self) -> List[Dict[str, Any]]:
        return [
            {"id": ws.workspace_id, "name": ws.name, "users": len(ws.users)}
            for ws in self._workspaces.values()
        ]
    
    def join(self, workspace_id: str, user_id: str, username: str) -> Optional[Dict[str, Any]]:
        ws = self._workspaces.get(workspace_id)
        if not ws:
            return None
        presence = ws.add_user(user_id, username)
        return {"ok": True, "presence": asdict(presence), "active_users": len(ws.get_active_users())}
    
    def leave(self, workspace_id: str, user_id: str) -> Dict[str, Any]:
        ws = self._workspaces.get(workspace_id)
        if not ws:
            return {"ok": False, "error": "workspace not found"}
        removed = ws.remove_user(user_id)
        return {"ok": removed}
    
    def heartbeat(self, workspace_id: str, user_id: str, line: int = 0, col: int = 0, file_path: str = ""):
        ws = self._workspaces.get(workspace_id)
        if ws:
            ws.update_cursor(user_id, line, col, file_path)
    
    def get_presence(self, workspace_id: str) -> Dict[str, Any]:
        ws = self._workspaces.get(workspace_id)
        if not ws:
            return {"ok": False, "error": "workspace not found"}
        active = ws.get_active_users()
        return {
            "ok": True,
            "workspace": ws.name,
            "total_users": len(ws.users),
            "active_users": len(active),
            "presences": [asdict(u) for u in active]
        }
    
    def delete_workspace(self, workspace_id: str) -> bool:
        if workspace_id in self._workspaces:
            del self._workspaces[workspace_id]
            return True
        return False


# Color generation for user avatars
_USER_COLORS = [
    "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
    "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9",
    "#F8C471", "#82E0AA", "#F1948A", "#AED6F1", "#D7BDE2",
]

def _generate_color(seed: str) -> str:
    idx = hash(seed) % len(_USER_COLORS)
    return _USER_COLORS[idx]
