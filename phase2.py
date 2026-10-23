
import os
import time
import psutil
import multiprocessing


def filewatcher_worker():
    """Background worker for the Permission Watch project."""
    print(
        f"\n[FileWatcher] Worker started | PID: {os.getpid()}",
        flush=True
    )

    while True:
        # Placeholder for future monitoring tasks
        time.sleep(2)


def main():
    worker = multiprocessing.Process(
        target=filewatcher_worker,
        name="FileWatcherWorker"
    )

    worker.start()
    start_time = time.monotonic()

    print("\n=== Permission Watch: Phase 2 ===")
    print("Linux Process Monitoring Module")
    print("-" * 48)
    print(f"Worker PID:        {worker.pid}")
    print(f"Parent Process ID: {os.getpid()}")
    print("-" * 48)

    process = psutil.Process(worker.pid)

    # Prime CPU measurement before collecting the first reading
    process.cpu_percent(interval=None)

    try:
        while worker.is_alive():
            time.sleep(1)

            if not worker.is_alive():
                break

            try:
                cpu = process.cpu_percent(interval=None)
                memory_mb = (
                    process.memory_info().rss / (1024 * 1024)
                )
                status = process.status()
                threads = process.num_threads()
                elapsed = time.monotonic() - start_time

                print(
                    f"Uptime: {elapsed:6.1f}s | "
                    f"State: {status:<10} | "
                    f"CPU: {cpu:5.1f}% | "
                    f"RAM: {memory_mb:7.2f} MB | "
                    f"Threads: {threads}"
                )

            except psutil.NoSuchProcess:
                print("Worker process has ended.")
                break

    except KeyboardInterrupt:
        print("\nStopping Permission Watch...")

    finally:
        if worker.is_alive():
            worker.terminate()

        worker.join()
        print("Worker stopped. Cleanup complete.")


if __name__ == "__main__":
    main()

