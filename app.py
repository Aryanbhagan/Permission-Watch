import threading
from config import get_watch_directory
from database import initialize_database
from file_monitor import monitor_files
from permission_monitor import monitor_permissions


def main():
    try:
        watch_dir = get_watch_directory()
    except ValueError as error:
        print(f"Error: {error}")
        return

    initialize_database()

    stop_event = threading.Event()

    file_thread = threading.Thread(
        target=monitor_files,
        args=(watch_dir, stop_event),
        name="FileMonitor",
    )

    permission_thread = threading.Thread(
        target=monitor_permissions,
        args=(watch_dir, stop_event),
        name="PermissionMonitor",
    )

    print("\n=== Permission Watch ===")
    print(f"Target directory: {watch_dir}")
    print("File and permission monitoring starting...")
    print("Press Ctrl+C to stop both monitors.\n")

    try:
        file_thread.start()
        permission_thread.start()

        while file_thread.is_alive() and permission_thread.is_alive():
            file_thread.join(timeout=0.5)
            permission_thread.join(timeout=0.5)

    except KeyboardInterrupt:
        print("\nStopping Permission Watch...")

    finally:
        stop_event.set()

        if file_thread.ident is not None:
            file_thread.join()

        if permission_thread.ident is not None:
            permission_thread.join()

        print("Permission Watch stopped.")


if __name__ == "__main__":
    main()
