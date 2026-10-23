from pathlib import Path

DEFAULT_WATCH_DIR = Path.home() / "FileWatcher" / "test_data"


def get_watch_directory():
    entered_path = input(
        "Enter directory to monitor "
        f"[{DEFAULT_WATCH_DIR}]: "
    ).strip()

    if not entered_path:
        selected_path = DEFAULT_WATCH_DIR
    else:
        selected_path = Path(entered_path).expanduser()

    selected_path = selected_path.resolve()

    if not selected_path.is_dir():
        raise ValueError(
            f"Directory does not exist: {selected_path}"
        )

    if not selected_path.is_absolute():
        raise ValueError("Please enter an absolute path.")

    return selected_path
