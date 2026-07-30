import pytest
from lappa.panels.foxglove_panel import FoxgloveBridgePanel, DEFAULT_BRIDGE_URL, FOXGLOVE_URL

def test_default_bridge_url():
    panel = FoxgloveBridgePanel()
    assert panel.bridge_url == DEFAULT_BRIDGE_URL

def test_custom_bridge_url():
    panel = FoxgloveBridgePanel("ws://localhost:9091")
    assert panel.bridge_url == "ws://localhost:9091"

def test_offline_status():
    panel = FoxgloveBridgePanel("ws://127.0.0.1:19999")
    assert not panel.connected

def test_get_status():
    panel = FoxgloveBridgePanel("ws://127.0.0.1:19999")
    status = panel.get_status()
    assert "bridge_url" in status
    assert "connected" in status
    assert "timestamp" in status
    assert not status["connected"]

def test_open_panel_offline():
    panel = FoxgloveBridgePanel("ws://127.0.0.1:19999")
    result = panel.open_panel()
    assert "OFFLINE" in result or "not reachable" in result

def test_get_topics_offline():
    panel = FoxgloveBridgePanel("ws://127.0.0.1:19999")
    topics = panel.get_topics()
    assert topics == []

def test_cli_help():
    from lappa.panels.foxglove_panel import cli
    import sys
    old = sys.argv
    sys.argv = ["foxglove_panel"]
    try:
        cli()
    except SystemExit:
        pass
    sys.argv = old
