"""Foxglove/rosbridge web panel stub (closes #10)."""
import webbrowser, json, time, urllib.request, urllib.error
from typing import Optional

DEFAULT_BRIDGE_URL = "ws://localhost:9090"
FOXGLOVE_URL = "https://studio.foxglove.dev"


class FoxgloveBridgePanel:
    """Optional panel connecting to rosbridge when Docker runtime is up."""
    
    def __init__(self, bridge_url: str = DEFAULT_BRIDGE_URL):
        self.bridge_url = bridge_url
        self.connected = False
        self._check_connection()
    
    def _check_connection(self):
        """Check if rosbridge server is reachable."""
        try:
            req = urllib.request.Request(self.bridge_url.replace("ws://", "http://").rstrip("/") + "/")
            with urllib.request.urlopen(req, timeout=2) as resp:
                self.connected = resp.status == 200
        except Exception:
            self.connected = False
    
    def open_panel(self) -> str:
        """Open Foxglove Studio in browser, or show offline message."""
        if self.connected:
            url = f"{FOXGLOVE_URL}/?rosbridge-websocket={self.bridge_url}"
            try:
                webbrowser.open(url)
                return f"Foxglove Studio opened at {url}"
            except Exception as e:
                return f"Error opening browser: {e}"
        else:
            return f"[OFFLINE] rosbridge server not reachable at {self.bridge_url}. Start Docker runtime first."
    
    def get_status(self) -> dict:
        """Return bridge connection status."""
        return {
            "bridge_url": self.bridge_url,
            "connected": self.connected,
            "foxglove_url": FOXGLOVE_URL,
            "timestamp": time.time(),
        }
    
    def get_topics(self) -> list[str]:
        """List ROS topics if connected."""
        if not self.connected:
            return []
        try:
            req = urllib.request.Request(
                self.bridge_url.replace("ws://", "http://").rstrip("/") + "/topics"
            )
            with urllib.request.urlopen(req, timeout=2) as resp:
                return json.loads(resp.read())
        except Exception:
            return []


def cli():
    import argparse
    parser = argparse.ArgumentParser(description="Lappa Foxglove Panel")
    parser.add_argument("--bridge-url", default=DEFAULT_BRIDGE_URL, help="rosbridge WebSocket URL")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("open", help="Open Foxglove Studio")
    sub.add_parser("status", help="Show bridge status")
    sub.add_parser("topics", help="List ROS topics")
    
    args = parser.parse_args()
    panel = FoxgloveBridgePanel(args.bridge_url)
    
    if args.cmd == "open":
        print(panel.open_panel())
    elif args.cmd == "status":
        s = panel.get_status()
        print(f"Bridge: {s['bridge_url']}")
        print(f"Status: {'CONNECTED' if s['connected'] else 'OFFLINE'}")
        print(f"Foxglove: {s['foxglove_url']}")
    elif args.cmd == "topics":
        topics = panel.get_topics()
        if topics:
            for t in topics:
                print(f"  - {t}")
        else:
            print("[OFFLINE] No topics available — bridge is down.")
    else:
        parser.print_help()

if __name__ == "__main__":
    cli()
