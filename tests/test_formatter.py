from ntfy_lite.formatter import AttachmentFormatter, TruncationFormatter


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

    assert len(result["data"]) < 4000
    assert "... [truncated] ..." in result["data"]
    assert result["data"].startswith("A" * 1800)
    assert result["data"].endswith("A" * 2100)
    assert result["message_header"] is None
    assert result["filename_header"] is None
    assert result["file_to_close"] is None
    assert result["temp_file_path"] is None


def test_attachment_formatter_short_message():
    formatter = AttachmentFormatter()
    message = "Short message"
    result = formatter.process(message)

    assert result["data"] == message
    assert result["message_header"] is None
    assert result["filename_header"] is None
    assert result["file_to_close"] is None
    assert result["temp_file_path"] is None


def test_truncation_formatter_long_unicode_message():
    formatter = TruncationFormatter()
    # A single emoji usually takes 4 bytes. 1000 emojis = 4000 bytes. 1500 emojis = 6000 bytes.
    message = "🐋" * 1500
    result = formatter.process(message)

    assert len(result["data"]) < 4000
    assert "... [truncated] ..." in result["data"]
    assert result["message_header"] is None
    assert result["filename_header"] is None
    assert result["file_to_close"] is None
    assert result["temp_file_path"] is None
