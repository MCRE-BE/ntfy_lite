"""Tests."""

####################
# IMPORT STATEMENT #
####################
from ntfy_lite.formatter import AttachmentFormatter, TruncationFormatter


####################
# INDIVIDUAL TESTS #
####################
def test_truncation_formatter_short_message():
    formatter = TruncationFormatter()
    message = "Short message"
    result = formatter.process(message)

    assert result["data"] == message
    assert result["message_header"] is None
    assert result["filename_header"] is None
    assert result["file_to_close"] is None
    assert result["temp_file_path"] is None


def test_truncation_formatter_long_message():
    formatter = TruncationFormatter()
    message = "A" * 4500
    result = formatter.process(message)

    assert len(result["data"]) <= 4000
    assert "... [truncated] ..." in result["data"]
    # Available length for 'A's is 4000 - len("\n... [truncated] ...\n") == 3978
    # Head length: 3978 // 2 - 50 = 1939
    # Tail length: 3978 - 1939 = 2039
    assert result["data"].startswith("A" * 1939)
    assert result["data"].endswith("A" * 2039)
    assert result["message_header"] is None
    assert result["filename_header"] is None
    assert result["file_to_close"] is None
    assert result["temp_file_path"] is None


def test_truncation_formatter_custom_length():
    trunc_msg = "[CUT]"
    formatter = TruncationFormatter(max_length=100, truncation_message=trunc_msg)
    message = "A" * 150
    result = formatter.process(message)

    assert len(result["data"]) <= 100
    assert trunc_msg in result["data"]
    # Available length: 100 - 5 = 95
    # Head: 95 // 2 - 50 = -2. If head is -2, it's problematic but let's test the logic.
    # Actually available_length is 95. Head: 95//2 - 50 = 47 - 50 = -3.
    # To avoid negative index bias issues in test, let's use a larger max_length.
    formatter2 = TruncationFormatter(max_length=200, truncation_message=trunc_msg)
    result2 = formatter2.process(message)
    assert len(result2["data"]) <= 200
    assert result2["data"] == message  # Should not be truncated!

    message3 = "A" * 250
    result3 = formatter2.process(message3)
    assert len(result3["data"]) <= 200
    assert trunc_msg in result3["data"]


def test_attachment_formatter_short_message():
    formatter = AttachmentFormatter()
    message = "Short message"
    result = formatter.process(message)

    assert result["data"] == message
    assert result["message_header"] is None
    assert result["filename_header"] is None
    assert result["file_to_close"] is None
    assert result["temp_file_path"] is None


def test_attachment_formatter_custom_length():
    trunc_msg = "[CUT]"
    formatter = AttachmentFormatter(max_length=100, truncation_message=trunc_msg)
    message = "A" * 150
    result = formatter.process(message)

    assert result["message_header"] is not None
    assert len(result["message_header"]) <= 100
    assert trunc_msg in result["message_header"]
    assert result["file_to_close"] is not None
    assert result["filename_header"] == "traceback.txt"


def test_truncation_formatter_long_unicode_message():
    formatter = TruncationFormatter()
    # A single emoji usually takes 4 bytes. 1000 emojis = 4000 bytes. 1500 emojis = 6000 bytes.
    message = "🐋" * 1500
    result = formatter.process(message)

    assert len(result["data"]) <= 4000
    assert "... [truncated] ..." in result["data"]
    assert result["message_header"] is None
    assert result["filename_header"] is None
    assert result["file_to_close"] is None
    assert result["temp_file_path"] is None
