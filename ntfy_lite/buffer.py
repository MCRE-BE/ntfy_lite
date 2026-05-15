"""Module defining the NtfyBuffer for SQLite background buffering."""

# %%
####################
# Import Statement #
####################
import json
import logging
import sqlite3
import sys
import threading
import time
import typing
from pathlib import Path

if sys.version_info >= (3, 11):
    from typing import Self
else:  # pragma: no cover
    from typing_extensions import Self

import requests


###########
# CLASSES #
###########
class NtfyBuffer:
    """Buffer to store and asynchronously retry failed NTFY messages.

    Why this exists:
    When sending bulk notifications or responding to parallel processes, the NTFY server
    frequently enforces an HTTP 429 "Too Many Requests" rate limit constraint. If left
    unhandled, or handled via a synchronous `time.sleep()`, the entire pipeline will
    freeze waiting for the server to accept the new payload.

    Setup:
    This class handles a dedicated local SQLite database that records failed messages.
    Instead of blocking execution, `ntfy.push()` can quickly offload the failed message
    into this class. It then triggers a daemon background thread (`_flush_buffer_thread`)
    which will discretely wait for rate limit cooldowns and retry pushing the messages
    in the background. The Database path is normally configured dynamically when passing
    the NtfyHandler to a logger instance and passed sequentially downwards.
    """

    def __init__(
        self: Self,
        db_path: Path,
        max_file_size: int = 5 * 1024 * 1024,
    ) -> None:
        """Start the buffer, setting up its SQLite path.

        Parameters
        ----------
        db_path : Path
            The file path to the SQLite database. Ensure this path is in a
            folder that persists across executions (like your standard logging
            directory) so messages survive unexpected application shutdowns.
        max_file_size : int, optional
            The maximum number of bytes to read from file attachments when buffering
            to prevent memory exhaustion. Defaults to 5MB.
        """
        self.db_path = Path(db_path)
        self.max_file_size = max_file_size
        self._flusher_lock = threading.Lock()
        self._flusher_state = {"running": False}
        self._session = requests.Session()
        self._init_db()
        self._trigger_buffer_flush()

    def _init_db(self: Self) -> None:
        """Initialize the SQLite database for buffering NTFY messages.

        This will ensure the directory path exists and create a singular `buffer` table
        housing the target URL, the topic, the serialized API headers, and the payload string.
        """
        try:
            self.db_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS buffer (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        topic TEXT,
                        url TEXT,
                        headers TEXT,
                        data TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
        except (OSError, sqlite3.Error, Exception):
            logging.exception("Failed to initialize ntfy SQLite buffer")

    def add(
        self: Self,
        topic: str,
        url: str,
        data: str | bytes,
        headers: typing.Mapping[str, str],
    ) -> None:
        """Stores the failed NTFY message in a local SQLite file to be retried asynchronously.

        If an HTTP 429 is raised inside `ntfy.push()`, it immediately executes this method to store
        the context into the SQLite file. Afterwards, it triggers the thread flusher to ensure
        the background retries begin processing immediately.
        """
        try:
            with sqlite3.connect(str(self.db_path), timeout=10) as conn:
                conn.execute(
                    "INSERT INTO buffer (topic, url, headers, data) VALUES (?, ?, ?, ?)",
                    (topic, url, json.dumps(headers), data),
                )
            self._trigger_buffer_flush()
        except (sqlite3.Error, Exception):
            logging.exception("Failed to buffer NTFY message")

    def _flush_buffer_thread(self: Self) -> None:
        """Background worker that reads from the SQLite buffer and retries messages.

        This routine:
        1. Selects all rows currently stranded in the buffer ordered by creation date.
        2. Attempts an HTTP PUT.
        3. If successful, sleeps briefly to avoid hitting rate limits on subsequent requests.
        4. If it's a 429, it sleeps for 60 seconds and breaks the loop (it will try again
           next pipeline run).
        5. Successes and untrappable HTTP failure codes will delete the row permanently
           to ensure no infinite looping records.
        """
        try:
            # We process in batches to keep memory usage low while still benefiting
            # from batch deletions and connection pooling.
            while True:
                rows = []
                try:
                    with sqlite3.connect(str(self.db_path), timeout=10) as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "SELECT id, topic, url, headers, data FROM buffer ORDER BY created_at ASC LIMIT 100",
                        )
                        rows = cursor.fetchall()
                except (sqlite3.Error, Exception):
                    logging.exception("Failed to fetch from ntfy SQLite buffer")
                    break

                if not rows:
                    break

                to_delete = []
                stop_flushing = False

                for row in rows:
                    row_done, stop_flushing = self._flush_row(row)
                    if row_done:
                        to_delete.append((row[0],))
                    if stop_flushing:
                        break

                if to_delete:
                    try:
                        with sqlite3.connect(str(self.db_path), timeout=10) as conn:
                            conn.executemany("DELETE FROM buffer WHERE id = ?", to_delete)
                    except (sqlite3.Error, Exception):
                        logging.exception("Failed to batch delete buffered messages.")
                        break

                if stop_flushing:
                    break
        except Exception:
            logging.exception("NTFY async flusher final exception fallback")
        finally:
            with self._flusher_lock:
                self._flusher_state["running"] = False

    def _flush_row(
        self: Self,
        row: tuple[int, str, str, str, str | bytes],
    ) -> tuple[bool, bool]:
        """Process a single buffered row.

        Returns
        -------
        tuple[bool, bool]
            (row_done, stop_flushing)
            row_done: if True, the row should be deleted from the buffer.
            stop_flushing: if True, the flusher should stop processing for now.
        """
        row_id, topic, url, headers_json, data = row
        try:
            headers = json.loads(headers_json)

            response = self._session.put(f"{url}/{topic}", data=data, headers=headers, timeout=10)
            if response.ok:
                # Pause slightly between successful flushes to prevent hitting HTTP 429
                # rate limits when rapidly emptying a large buffer queue
                time.sleep(2)
                return True, False
            if int(response.status_code) == 429:
                # Still rate limited; stop flushing so we don't spam the server further
                logging.warning("NTFY buffer fast retry rate limited (HTTP 429). Will stop flusher.")
                time.sleep(60)
                return False, True

            # Some other failure, discard the buffered message and log the trace
            logging.error(
                f"NTFY async retry failed: {response.reason}. Discarding buffered message id {row_id}.",
            )
        except (requests.RequestException, json.JSONDecodeError, Exception):
            logging.exception("NTFY async flusher exception.")
            return False, True

        return True, False

    def _trigger_buffer_flush(self: Self) -> None:
        """Spawns the background synchronization thread if it isn't running already."""
        with self._flusher_lock:
            if not self._flusher_state["running"]:
                self._flusher_state["running"] = True
                t = threading.Thread(target=self._flush_buffer_thread, daemon=True)
                t.start()
