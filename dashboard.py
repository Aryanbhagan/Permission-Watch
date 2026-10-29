import os
import threading
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from database import initialize_database
from file_monitor import monitor_files
from permission_monitor import monitor_permissions

app = Flask(__name__)

DB_PATH = Path(__file__).parent / "permission_watch.db"

# Restrict folder browsing to the user's home directory.
HOME_DIR = Path.home().resolve()

monitor_lock = threading.Lock()
monitor_state = {
    "active": False,
    "directory": None,
    "error": None,
}

monitor_stop_event = None
monitor_threads = []


def get_db_connection():
    import sqlite3

    connection = sqlite3.connect(DB_PATH, timeout=5)
    connection.row_factory = sqlite3.Row
    return connection


def resolve_allowed_directory(raw_path):
    """Resolve a directory and ensure it stays inside the home directory."""
    if not raw_path:
        raise ValueError("Please provide a directory path.")

    path = Path(raw_path).expanduser().resolve(strict=True)

    if not path.is_dir():
        raise ValueError("Selected path is not a directory.")

    try:
        path.relative_to(HOME_DIR)
    except ValueError:
        raise ValueError("Only directories inside your home folder are allowed.")

    return path


def monitoring_worker(watch_dir, stop_event):
    """Run both monitoring functions using one shared stop event."""
    global monitor_state

    try:
        initialize_database()

        threads = [
            threading.Thread(
                target=monitor_files,
                args=(watch_dir, stop_event),
                name="FileMonitor",
            ),
            threading.Thread(
                target=monitor_permissions,
                args=(watch_dir, stop_event),
                name="PermissionMonitor",
            ),
        ]

        with monitor_lock:
            monitor_state["active"] = True
            monitor_state["directory"] = str(watch_dir)
            monitor_state["error"] = None

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

    except Exception as error:
        with monitor_lock:
            monitor_state["error"] = str(error)

        print(f"Monitoring error: {error}", flush=True)

    finally:
        stop_event.set()

        with monitor_lock:
            monitor_state["active"] = False


@app.route("/")
def dashboard():
    return render_template("dashboard.html")


@app.route("/api/browse")
def browse_directories():
    raw_path = request.args.get("path", str(HOME_DIR))

    try:
        directory = resolve_allowed_directory(raw_path)

        folders = []

        with os.scandir(directory) as entries:
            for entry in entries:
                try:
                    if entry.is_dir(follow_symlinks=False):
                        folders.append({
                            "name": entry.name,
                            "path": str(Path(entry.path)),
                        })
                except OSError:
                    continue

        folders.sort(key=lambda item: item["name"].lower())

        return jsonify({
            "current": str(directory),
            "parent": (
                str(directory.parent)
                if directory != HOME_DIR
                else None
            ),
            "folders": folders,
        })

    except (ValueError, OSError, RuntimeError) as error:
        return jsonify({"error": str(error)}), 400


@app.route("/api/monitor/start", methods=["POST"])
def start_monitoring():
    global monitor_stop_event, monitor_threads

    data = request.get_json(silent=True) or {}

    try:
        watch_dir = resolve_allowed_directory(data.get("path", ""))
    except (ValueError, OSError, RuntimeError) as error:
        return jsonify({"error": str(error)}), 400

    with monitor_lock:
        if monitor_state["active"]:
            return jsonify({
                "error": "Monitoring is already active.",
                "directory": monitor_state["directory"],
            }), 409

        monitor_stop_event = threading.Event()

        worker = threading.Thread(
            target=monitoring_worker,
            args=(watch_dir, monitor_stop_event),
            name="PermissionWatchManager",
            daemon=True,
        )

        monitor_threads = [worker]
        worker.start()

    return jsonify({
        "message": "Monitoring started.",
        "directory": str(watch_dir),
    }), 202


@app.route("/api/monitor/stop", methods=["POST"])
def stop_monitoring():
    with monitor_lock:
        if not monitor_state["active"] or monitor_stop_event is None:
            return jsonify({"message": "Monitoring is not active."})

        monitor_stop_event.set()

    return jsonify({"message": "Stop requested."}), 200


@app.route("/api/monitor/status")
def monitoring_status():
    with monitor_lock:
        return jsonify({
            "active": monitor_state["active"],
            "directory": monitor_state["directory"],
            "error": monitor_state["error"],
        })


@app.route("/api/stats")
def get_stats():
    with get_db_connection() as connection:
        total_events = connection.execute(
            "SELECT COUNT(*) FROM events"
        ).fetchone()[0]

        high_risk = connection.execute(
            "SELECT COUNT(*) FROM events "
            "WHERE UPPER(risk_level) LIKE 'HIGH%'"
        ).fetchone()[0]

        medium_risk = connection.execute(
            "SELECT COUNT(*) FROM events "
            "WHERE UPPER(risk_level) LIKE 'MEDIUM%'"
        ).fetchone()[0]

        permission_events = connection.execute(
            "SELECT COUNT(*) FROM events "
            "WHERE event_type LIKE '%PERMISSION%'"
        ).fetchone()[0]

        file_events = connection.execute(
            "SELECT COUNT(*) FROM events "
            "WHERE event_type LIKE 'FILE_%'"
        ).fetchone()[0]

    return jsonify({
        "total_events": total_events,
        "high_risk": high_risk,
        "medium_risk": medium_risk,
        "permission_events": permission_events,
        "file_events": file_events,
    })


@app.route("/api/events")
def get_events():
    limit = request.args.get("limit", default=100, type=int)
    limit = max(1, min(limit, 500))

    with get_db_connection() as connection:
        rows = connection.execute("""
            SELECT id, timestamp, event_type, file_path,
                   old_value, new_value, risk_level
            FROM events
            ORDER BY id DESC
            LIMIT ?
        """, (limit,)).fetchall()

    return jsonify([dict(row) for row in rows])


@app.route("/api/analytics")
def get_analytics():
    with get_db_connection() as connection:
        risk_rows = connection.execute("""
            SELECT
                CASE
                    WHEN UPPER(risk_level) LIKE 'HIGH%' THEN 'HIGH'
                    WHEN UPPER(risk_level) LIKE 'MEDIUM%' THEN 'MEDIUM'
                    WHEN UPPER(risk_level) LIKE 'LOW%' THEN 'LOW'
                    ELSE 'INFO'
                END AS risk,
                COUNT(*) AS count
            FROM events
            GROUP BY risk
        """).fetchall()

        type_rows = connection.execute("""
            SELECT event_type, COUNT(*) AS count
            FROM events
            GROUP BY event_type
            ORDER BY count DESC
        """).fetchall()

    return jsonify({
        "risk_distribution": [dict(row) for row in risk_rows],
        "event_types": [dict(row) for row in type_rows],
    })


if __name__ == "__main__":
    initialize_database()
    print("Permission Watch Dashboard starting...")
    print(f"Database: {DB_PATH}")
    app.run(host="127.0.0.1", port=5000, debug=False)
