# Permission Watch

**Permission Watch** is a Python-based Linux monitoring project that detects filesystem activity and changes in file permissions and ownership. It stores detected events in an SQLite database for later review.

The project is developed and tested in Ubuntu using WSL2.

## Features

- Detects file creation, modification, deletion and renaming.
- Monitors file permission changes.
- Detects changes in file ownership and group ownership.
- Assigns basic risk labels to selected permission configurations.
- Stores monitoring events in an SQLite database.
- Allows the user to select a target directory when starting the application.
- Includes a process-monitoring prototype using `psutil`.

## Technologies Used

- Python 3
- Linux / Ubuntu on WSL2
- Watchdog
- psutil
- SQLite
- Python multiprocessing and threading

## Project Structure

```text
FileWatcher/
├── app.py
├── config.py
├── database.py
├── file_monitor.py
├── permission_monitor.py
├── phase2.py
├── README.md
└── .gitignore
```

## Requirements

- Python 3
- Ubuntu or a compatible Linux environment
- Watchdog
- psutil

Install the required packages on Ubuntu:

```bash
sudo apt update
sudo apt install python3-watchdog python3-psutil
```

## How to Run

1. Clone the Repository

git clone https://github.com/Aryanbhagan/Permission-Watch.git
cd Permission-Watch

2. Set Up the Environment

Create and activate a Python virtual environment:

python3 -m venv .venv
source .venv/bin/activate

Install the required dependencies:

pip install flask watchdog psutil

3. Start the Web Dashboard

Run the dashboard:

python dashboard.py

Open your browser and visit:

http://127.0.0.1:5000

Select a directory, start monitoring, and view file activity and permission-related events through the dashboard. Use the dashboard controls to start or stop monitoring.

Keep the terminal running while using the dashboard. Press Ctrl+C to stop the dashboard server.

4. Run in Terminal Mode

To use the original terminal-based monitoring application instead:

python3 app.py

Enter the absolute path of an existing directory when prompted. Press Enter to use the default test_data directory.

## Database

Events are stored in `permission_watch.db`, which is created locally when the application runs.

The database records timestamps, event types, file paths, previous and new values, and risk labels where applicable.

The local database is excluded from version control.

## Current Limitations

- The file and permission monitors use separate monitoring threads.
- Permission monitoring relies on periodic snapshots and may miss changes that occur and are reversed between scans.
- The application records detected changes but does not prevent them.
- The process-monitoring module is currently a separate prototype.
- The web dashboard has not yet been implemented.

## Future Enhancements

- Develop a web dashboard using Flask.
- Improve duplicate-event handling.
- Improve monitoring reliability and error handling.
- Add event filtering and summary statistics.
- Integrate additional process-monitoring capabilities.

## Project Status

The current version includes an integrated launcher, configurable directory selection, filesystem event monitoring, permission and ownership monitoring, and SQLite event logging.
