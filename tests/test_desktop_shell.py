import pytest
from lappa.desktop.shell import find_free_port, DEFAULT_PORT, DEFAULT_HOST

def test_find_free_port():
    port = find_free_port()
    assert isinstance(port, int)
    assert port >= DEFAULT_PORT

def test_default_constants():
    assert DEFAULT_PORT == 8501
    assert DEFAULT_HOST == "127.0.0.1"

def test_cli_help():
    from lappa.desktop.shell import cli
    import sys
    old = sys.argv
    sys.argv = ["shell"]
    try: cli()
    except SystemExit: pass
    sys.argv = old
