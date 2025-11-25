#!/usr/bin/env python
"""
Alembic migration management script.

Usage:
  python manage_migrations.py upgrade       # Run migrations to latest
  python manage_migrations.py downgrade -1  # Downgrade by 1 revision
  python manage_migrations.py revision -m "message"  # Create new revision
  python manage_migrations.py current       # Show current revision
"""

import sys
import subprocess
from pathlib import Path

def run_command(cmd):
    """Run alembic command."""
    result = subprocess.run(cmd, shell=True)
    sys.exit(result.returncode)

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    args = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
    
    cmd = f".venv\\Scripts\\alembic {command} {args}"
    print(f"Running: {cmd}")
    run_command(cmd)

if __name__ == "__main__":
    main()
