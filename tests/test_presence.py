"""Tests for collaborative workspace presence."""
import time
import pytest
from lappa.presence import (
    PresenceService, WorkspaceState, UserPresence, _generate_color
)


class TestUserPresence:
    
    def test_active_when_recent(self):
        user = UserPresence(user_id="u1", username="alice")
        assert user.is_active is True
    
    def test_inactive_after_timeout(self):
        user = UserPresence(user_id="u1", username="bob", last_seen=0)
        assert user.is_active is False
    
    def test_color_assignment(self):
        user = UserPresence(user_id="u1", username="carol", color="#FF0000")
        assert user.color == "#FF0000"


class TestWorkspaceState:
    
    def test_add_user(self):
        ws = WorkspaceState(workspace_id="w1", name="test")
        presence = ws.add_user("u1", "alice")
        assert presence.username == "alice"
        assert "u1" in ws.users
    
    def test_remove_user(self):
        ws = WorkspaceState(workspace_id="w1", name="test")
        ws.add_user("u1", "alice")
        assert ws.remove_user("u1") is True
        assert ws.remove_user("u1") is False
    
    def test_get_active_users(self):
        ws = WorkspaceState(workspace_id="w1", name="test")
        ws.add_user("u1", "alice")
        inactive = UserPresence(user_id="u2", username="bob", last_seen=0)
        ws.users["u2"] = inactive
        active = ws.get_active_users()
        assert len(active) == 1
        assert active[0].username == "alice"
    
    def test_update_cursor(self):
        ws = WorkspaceState(workspace_id="w1", name="test")
        ws.add_user("u1", "alice")
        ws.update_cursor("u1", 42, 10, "main.py")
        assert ws.users["u1"].cursor_line == 42
        assert ws.users["u1"].active_file == "main.py"


class TestPresenceService:
    
    def setup_method(self):
        self.svc = PresenceService()
    
    def test_create_and_get_workspace(self):
        ws = self.svc.create_workspace("My Project")
        retrieved = self.svc.get_workspace(ws.workspace_id)
        assert retrieved is not None
        assert retrieved.name == "My Project"
    
    def test_list_workspaces(self):
        self.svc.create_workspace("Project A")
        self.svc.create_workspace("Project B")
        workspaces = self.svc.list_workspaces()
        assert len(workspaces) == 2
    
    def test_join_and_leave(self):
        ws = self.svc.create_workspace("Test")
        result = self.svc.join(ws.workspace_id, "u1", "alice")
        assert result["ok"] is True
        assert result["active_users"] == 1
        
        leave_result = self.svc.leave(ws.workspace_id, "u1")
        assert leave_result["ok"] is True
    
    def test_heartbeat(self):
        ws = self.svc.create_workspace("Test")
        self.svc.join(ws.workspace_id, "u1", "alice")
        self.svc.heartbeat(ws.workspace_id, "u1", 10, 5, "src/main.py")
        
        presence = self.svc.get_presence(ws.workspace_id)
        assert presence["ok"] is True
        assert presence["active_users"] == 1
    
    def test_get_presence_empty(self):
        ws = self.svc.create_workspace("Empty")
        presence = self.svc.get_presence(ws.workspace_id)
        assert presence["active_users"] == 0
    
    def test_join_nonexistent_workspace(self):
        result = self.svc.join("nonexistent", "u1", "alice")
        assert result is None
    
    def test_delete_workspace(self):
        ws = self.svc.create_workspace("Temp")
        assert self.svc.delete_workspace(ws.workspace_id) is True
        assert self.svc.get_workspace(ws.workspace_id) is None
    
    def test_multiple_users(self):
        ws = self.svc.create_workspace("Collab")
        self.svc.join(ws.workspace_id, "u1", "alice")
        self.svc.join(ws.workspace_id, "u2", "bob")
        self.svc.join(ws.workspace_id, "u3", "carol")
        
        presence = self.svc.get_presence(ws.workspace_id)
        assert presence["total_users"] == 3
        assert presence["active_users"] == 3
    
    def test_color_generation(self):
        c1 = _generate_color("user1")
        c2 = _generate_color("user2")
        assert c1.startswith("#")
        assert c1 != c2  # Different users get different colors (usually)
