import os
import sys

# ensure the backend directory itself is on sys.path so `import app` works
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Optionally, you can also adjust the working directory to this root
# in case pytest changes it when locating tests.
os.chdir(ROOT)


# fixtures for starting/stopping the server could go here if needed
def pytest_configure(config):
    # ensure tests know where the backend root is
    config.backend_root = ROOT


def pytest_ignore_collect(collection_path, config):
    # Only collect tests that reside in the `backend/tests` directory.  The
    # project contains several standalone scripts named `test_*.py` at the
    # workspace root (e.g. `backend/test_paper_trade.py`).  Those should not
    # be treated as pytest test modules because they execute on import and
    # require a running server.  Skipping them keeps `pytest` runs clean.
    p = str(collection_path)
    tests_dir = os.path.join(ROOT, "tests")
    if not p.startswith(tests_dir):
        return True
    return False


import subprocess
import time
import socket
import atexit


def _wait_for_port(host: str, port: int, timeout: float = 10.0) -> bool:
    """Wait until a TCP port is accepting connections."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except Exception:
            time.sleep(0.1)
    return False


def _start_uvicorn_for_tests():
    # start uvicorn pointing at app.main:app on port 8000
    uvicorn_cmd = [
        sys.executable,
        '-m',
        'uvicorn',
        'app.main:app',
        '--host',
        '127.0.0.1',
        '--port',
        '8000',
        '--reload',
    ]
    env = os.environ.copy()
    # ensure PYTHONPATH includes ROOT so the app imports reliably
    env['PYTHONPATH'] = ROOT
    proc = subprocess.Popen(uvicorn_cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def _cleanup():
        try:
            proc.terminate()
        except Exception:
            pass

    atexit.register(_cleanup)
    # wait for it to become available
    if not _wait_for_port('127.0.0.1', 8000, timeout=10.0):
        proc.terminate()
        raise RuntimeError('uvicorn did not start on port 8000')
    return proc


import pytest


@pytest.fixture(scope='session', autouse=False)
def live_server():
    """Session fixture to start a live uvicorn server for integration tests.

    Usage: request this fixture in tests that need a running backend. It will
    start uvicorn on localhost:8000 and tear it down at session end.
    """
    proc = _start_uvicorn_for_tests()
    yield
    try:
        proc.terminate()
        proc.wait(timeout=5)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass

