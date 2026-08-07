# Impl-30: Collaborative Workspace Presence (optional)

## Overview

Feature #30 adds **collaborative workspace presence** to Lappa — the ability to see
which contributors are active in a shared workspace and what they are working on.
This feature is **optional** and can be enabled/disabled per workspace.

## Design

### Architecture

```
lappa/collab/
├── __init__.py          # Package init, feature-gate flag
├── presence.py          # Presence heartbeat + peer tracking
├── protocol.py          # Lightweight message protocol (JSON over WebSocket)
└── ui/
    └── presence_panel.py  # Qt panel showing online peers
```

### Presence States

| State      | Description                              |
|------------|------------------------------------------|
| `active`   | User is actively editing/viewing         |
| `idle`     | No activity for > 5 minutes              |
| `offline`  | User disconnected / left workspace       |

### Heartbeat Protocol

- Clients emit a heartbeat every **30 seconds** via WebSocket.
- Payload: `{user_id, workspace_id, status, timestamp, cursor_position, active_file}`
- Server broadcasts peer presence to all connected clients in the same workspace.
- Stale peers (no heartbeat for > 60s) are marked `offline`.

### Feature Gate

```python
# lappa/collab/__init__.py
COLLAB_ENABLED = os.environ.get("LAPPA_COLLAB", "0") == "1"
```

The feature is **disabled by default** (no network overhead). Enable with:
```bash
export LAPPA_COLLAB=1
lappa-gui
```

## Implementation Plan

1. **Module scaffold** — `lappa/collab/` package with feature gate
2. **Presence engine** — heartbeat timer, peer state machine
3. **Protocol layer** — JSON message serialization over WebSocket
4. **Qt UI panel** — `presence_panel.py` with avatars + status indicators
5. **Integration** — wire into main window, behind feature gate
6. **Tests** — unit tests for protocol, heartbeat, state machine
7. **CI** — dedicated workflow (`ci-30.yml`) for collaborative features

## Testing

```bash
# Run collab-specific tests
pytest tests/test_collab/ -v

# Enable collab for manual testing
LAPPA_COLLAB=1 pytest tests/test_collab/ -v
```

## Related

- Issue: [mergeos-bounties/Lappa #30](https://github.com/mergeos-bounties/Lappa/issues/30)
- Parent CI: `.github/workflows/ci.yml`
- Feature gate pattern: `lappa/env.py` (existing)
