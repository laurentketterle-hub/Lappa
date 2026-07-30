"""Lappa Desktop Shell — Electron/Tauri launcher (closes #14)."""
import subprocess, webbrowser, time, socket, sys, os

DEFAULT_PORT = 8501
DEFAULT_HOST = "127.0.0.1"

def find_free_port(start: int = DEFAULT_PORT) -> int:
    port = start
    while port < start + 100:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex((DEFAULT_HOST, port)) != 0:
                return port
            port += 1
    raise RuntimeError(f"No free port found in range {start}-{start+100}")

def start_server(port: int = None, host: str = DEFAULT_HOST) -> subprocess.Popen:
    if port is None:
        port = find_free_port()
    cmd = [sys.executable, "-m", "lappa.server", "--host", host, "--port", str(port)]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for _ in range(30):
        try:
            with socket.create_connection((host, port), timeout=0.5):
                break
        except (socket.error, OSError):
            time.sleep(0.2)
    else:
        proc.terminate()
        raise RuntimeError(f"Server failed to start on {host}:{port}")
    return proc

def launch_desktop(port: int = None):
    host = DEFAULT_HOST
    if port is None:
        port = find_free_port()
    print(f"Starting Lappa IDE on http://{host}:{port}")
    proc = start_server(port, host)
    url = f"http://{host}:{port}"
    try:
        webbrowser.open(url)
        print(f"Lappa IDE running at {url}")
        print("Press Ctrl+C to stop")
        proc.wait()
    except KeyboardInterrupt:
        print("\nShutting down...")
        proc.terminate()
        proc.wait()

def cli():
    import argparse
    parser = argparse.ArgumentParser(description="Lappa Desktop Shell")
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--host", default=DEFAULT_HOST)
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("start")
    sub.add_parser("launch")
    sub.add_parser("port")
    args = parser.parse_args()
    if args.cmd == "port":
        print(find_free_port())
    elif args.cmd == "start":
        proc = start_server(args.port, args.host)
        print(f"Server PID: {proc.pid}")
    elif args.cmd == "launch":
        launch_desktop(args.port)
    else:
        parser.print_help()

if __name__ == "__main__":
    cli()
