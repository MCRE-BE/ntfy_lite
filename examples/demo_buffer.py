"""ntfy lite: async buffering example"""

import time
import ntfy_lite as ntfy
from ntfy_lite.buffer import NtfyBuffer
from pathlib import Path

topic = "ntfy_lite_demo_buffer"


def run():
    print(f"pushing multiple messages to https://ntfy.sh/{topic} with a buffer")

    # We create a buffer using a local SQLite database file in the user's home directory.
    # When ntfy.sh returns 429 Too Many Requests (e.g. because we send too many in a short time),
    # the buffer will automatically persist the messages and retry in the background.
    buffer_path = Path.home() / ".ntfy_lite" / "demo_buffer.db"
    buffer_path.parent.mkdir(parents=True, exist_ok=True)

    buffer = NtfyBuffer(db_path=buffer_path)

    # Send multiple messages very quickly
    for i in range(1, 11):
        print(f"Queueing message {i}...")
        ntfy.push(
            topic,
            f"Buffer Demo - Message {i}",
            message=f"This is message {i} out of 10",
            tags=["fast_forward"],
            buffer=buffer,
        )

    print("All messages queued. The buffer daemon will flush them in the background.")

    # Wait for the buffer daemon thread to start pushing
    # Note: In real usage you don't need to block/wait, but here we keep the script alive.
    print("Waiting 10 seconds to allow the background daemon to process the buffer...")
    time.sleep(10)

    print("Done. You can check the buffer daemon logs or the topic.")


if __name__ == "__main__":
    run()
