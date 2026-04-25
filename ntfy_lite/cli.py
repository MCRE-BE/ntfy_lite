"""CLI interface for pushing ntfy notifications."""

import argparse
import sys
from pathlib import Path

from ntfy_lite import Priority, push


def main() -> None:
    """
    Main entry point for the `ntfy-lite` command-line interface.

    This function parses command-line arguments corresponding to the
    parameters of the `ntfy_lite.push` function. It executes the
    notification push and outputs a success or error message to standard
    streams.

    Raises
    ------
    SystemExit
        If the push notification fails due to network, validation, or other errors,
        the script will exit with status code 1.
    """
    parser = argparse.ArgumentParser(
        description="Push a notification using ntfy_lite.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("topic", help="The ntfy topic to push to.")
    parser.add_argument("title", help="The title of the notification.")
    parser.add_argument("-m", "--message", help="The message body of the notification.", default=None)
    parser.add_argument(
        "-p",
        "--priority",
        choices=[p.name.lower() for p in Priority],
        default=Priority.DEFAULT.name.lower(),
        help="The priority of the notification.",
    )
    parser.add_argument("-t", "--tags", help="Comma-separated list of tags (e.g., warning,skull).", default=None)
    parser.add_argument("-c", "--click", help="URL to open when the notification is clicked.", default=None)
    parser.add_argument("-e", "--email", help="Email address to forward the notification to.", default=None)
    parser.add_argument(
        "-f", "--filepath", type=Path, help="Path to a file to attach to the notification.", default=None
    )
    parser.add_argument("-a", "--attach", help="URL of a file to attach.", default=None)
    parser.add_argument("-i", "--icon", help="URL of an image to use as the notification icon.", default=None)
    parser.add_argument("--at", help="Timestamp or duration for delayed delivery.", default=None)
    parser.add_argument("-u", "--url", help="The ntfy server URL.", default="https://ntfy.sh")

    args = parser.parse_args()

    # Convert Priority
    priority = Priority[args.priority.upper()]

    # Convert tags to a list of strings
    tags = None
    if args.tags:
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]

    try:
        push(
            topic=args.topic,
            title=args.title,
            message=args.message,
            priority=priority,
            tags=tags,
            click=args.click,
            email=args.email,
            filepath=args.filepath,
            attach=args.attach,
            icon=args.icon,
            at=args.at,
            url=args.url,
        )
        sys.stdout.write("Notification pushed successfully.\n")
    except Exception as e:
        sys.stderr.write(f"Error pushing notification: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
