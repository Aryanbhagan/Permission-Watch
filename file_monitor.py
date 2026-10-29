
import time
import threading
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from database import initialize_database, log_event
from config import get_watch_directory



class PermissionWatchHandler(FileSystemEventHandler):

    IGNORED_FILES = {
        "permission_watch.db",
        "permission_watch.db-journal",
        "permission_watch.db-wal",
        "permission_watch.db-shm",
    }

    def should_ignore(self, path):
        return Path(path).name in self.IGNORED_FILES

    def on_created(self, event):
        if not event.is_directory:
            self.record_event(
                "FILE_CREATED", event.src_path
            )

    def on_modified(self, event):
        if not event.is_directory:
            self.record_event(
                "FILE_MODIFIED", event.src_path
            )

    def on_deleted(self, event):
        if not event.is_directory:
            self.record_event(
                "FILE_DELETED", event.src_path
            )

    def on_moved(self, event):
        if not event.is_directory and not self.should_ignore(event.src_path):
            self.record_event(
                "FILE_RENAMED",
                event.src_path,
                new_value=event.dest_path
            )

    def record_event(self, event_type, path, new_value=None):
        print(f"[{event_type}] {path}", flush=True)

        try:
            log_event(
                event_type=event_type,
                file_path=path,
                old_value=path if event_type == "FILE_RENAMED" else None,
                new_value=new_value,
                risk_level="INFO"
            )
            print("  Database: Event saved", flush=True)

        except Exception as error:
            print(f"  Database logging failed: {error}", flush=True)

def monitor_files(watch_dir, stop_event):
    initialize_database()

    handler = PermissionWatchHandler()
    observer = Observer()
    observer.schedule(handler, str(watch_dir), recursive=True)
    observer.start()

    print("=== Permission Watch: File Monitor ===")
    print(f"Monitoring: {watch_dir}")

    try:
        while not stop_event.wait(0.5):
            pass
    finally:
        observer.stop()
        observer.join()
        print("File monitor stopped.")


def main():
    try:
        watch_dir = get_watch_directory()
    except ValueError as error:
        print(f"Error: {error}")
        return

    try:
        monitor_files(watch_dir, threading.Event())
    except KeyboardInterrupt:
        print("\nStopping file monitor...")


if __name__ == "__main__":
    main()
