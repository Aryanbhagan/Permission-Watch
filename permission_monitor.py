
import os
import time
import stat
import pwd
import grp
import threading
from pathlib import Path
from datetime import datetime
from database import initialize_database, log_event
from config import get_watch_directory

SCAN_INTERVAL = 2


def get_file_details(path):
    """Collect permission bits and numeric owner/group IDs."""
    info = path.stat()

    return {
        "permissions": stat.S_IMODE(info.st_mode),
        "uid": info.st_uid,
        "gid": info.st_gid,
    }


def get_name(database, identifier):
    """Convert a user/group ID to a readable name."""
    try:
        return database(identifier).pw_name if database == pwd.getpwuid else database(identifier).gr_name
    except (KeyError, OSError):
        return str(identifier)

def scan_files(watch_dir):
    """Take a snapshot of files and directories, excluding SQLite files."""
    snapshot = {}

    ignored_files = {
        "permission_watch.db",
        "permission_watch.db-journal",
        "permission_watch.db-wal",
        "permission_watch.db-shm",
    }

    for root, dirs, files in os.walk(watch_dir):
        dirs[:] = [
            name for name in dirs
            if name not in {".venv", "__pycache__", "backups"}
        ]

        for name in dirs + files:
            if name in ignored_files:
                continue

            path = Path(root) / name

            try:
                snapshot[str(path)] = get_file_details(path)
            except (FileNotFoundError, PermissionError, OSError):
                continue

    return snapshot


def check_risk(permissions):
    """Flag potentially risky write permissions."""
    if permissions & stat.S_IWOTH:
        return "HIGH: Writable by everyone"

    if permissions & stat.S_IWGRP:
        return "MEDIUM: Writable by group"

    return "LOW"


def report_change(timestamp, path, attribute, old, new, risk=None):
    print(f"[{timestamp}] {attribute} CHANGED")
    print(f"  File: {path}")
    print(f"  Old:  {old}")
    print(f"  New:  {new}")

    if risk:
        print(f"  Risk: {risk}")
    try:
        log_event(
            event_type=f"{attribute}_CHANGED",
            file_path=path,
            old_value=old,
            new_value=new,
            risk_level=risk or "INFO"
        )
        print("  Database: Event saved")

    except Exception as error:
        print(f"  Database logging failed: {error}")

    print("-" * 45, flush=True)


def monitor_permissions(watch_dir, stop_event):
    initialize_database()

    print("=== Permission Watch: Security Monitor ===")
    print(f"Monitoring: {watch_dir}")
    print(f"Scan interval: {SCAN_INTERVAL} seconds")

    previous = scan_files(watch_dir)
    print(f"Initial snapshot: {len(previous)} items\n")

    while not stop_event.wait(SCAN_INTERVAL):
        current = scan_files(watch_dir)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for path, new in current.items():
            old = previous.get(path)

            if old is None:
                continue

            if old["permissions"] != new["permissions"]:
                report_change(
                    timestamp, path, "PERMISSION",
                    f"{old['permissions']:03o}",
                    f"{new['permissions']:03o}",
                    check_risk(new["permissions"]),
                )

            if old["uid"] != new["uid"]:
                report_change(
                    timestamp, path, "OWNER",
                    get_name(pwd.getpwuid, old["uid"]),
                    get_name(pwd.getpwuid, new["uid"]),
                )

            if old["gid"] != new["gid"]:
                report_change(
                    timestamp, path, "GROUP",
                    get_name(grp.getgrgid, old["gid"]),
                    get_name(grp.getgrgid, new["gid"]),
                )

        previous = current


def main():
    try:
        watch_dir = get_watch_directory()
    except ValueError as error:
        print(f"Error: {error}")
        return

    try:
        monitor_permissions(watch_dir, threading.Event())
    except KeyboardInterrupt:
        print("\nSecurity monitoring stopped.")


if __name__ == "__main__":
    main()
