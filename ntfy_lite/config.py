"""Module defining configurations, including types, logging levels, priorities and tags."""

import logging
import typing
from enum import Enum

LoggingLevel = typing.Literal[
    logging.DEBUG,
    logging.INFO,
    logging.NOTSET,
    logging.WARNING,
    logging.ERROR,
    logging.CRITICAL,
]
"""
Union of all logging levels (DEBUG, INFO, NOTSET,
WARNING, ERROR and CRITICAL)
"""


class Priority(Enum):
    """Enumeration of supported ntfy priority levels."""

    MAX = "5"
    """MAX"""

    HIGH = "4"
    """HIGH"""

    DEFAULT = "3"
    """DEFAULT"""

    LOW = "2"
    """LOW"""

    MIN = "1"
    """MIN"""


level2priority: dict[typing.Any, Priority] = {
    logging.CRITICAL: Priority.MAX,
    logging.ERROR: Priority.HIGH,
    logging.WARNING: Priority.HIGH,
    logging.INFO: Priority.DEFAULT,
    logging.DEBUG: Priority.LOW,
    logging.NOTSET: Priority.MIN,
}
"""
Default mapping from logging level to ntfy priority level
(e.g. a record of level INFO maps to a notification of piority
level 3)
"""

level2tags: dict[typing.Any, tuple[str, ...]] = {
    logging.CRITICAL: ("fire",),
    logging.ERROR: ("broken_heart",),
    logging.WARNING: ("warning",),
    logging.INFO: ("artificial_satellite",),
    logging.DEBUG: ("speech_balloon",),
    logging.NOTSET: (),
}
"""
Default mapping from logging level to tags, i.e. tags
that will be added to notifications corresponding to the
key logging level.

See [ntfy_lite.handler.NtfyHandler][]
"""
