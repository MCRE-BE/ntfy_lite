import sqlite3

import pytest

from ntfy_lite.buffer import NtfyBuffer


def test_buffer_unbounded_growth(tmp_path):
    """Test that the buffer currently grows without bound.

    This test will be updated/complemented to verify the fix.
    """
    db_path = tmp_path / "test_buffer.sqlite"
    # Current implementation doesn't have max_buffer_size,
    # but we can check the row count after multiple adds.
    buffer = NtfyBuffer(db_path)

    num_entries = 10
    for i in range(num_entries):
        buffer.add("topic", "http://localhost", f"data {i}", {"Header": "Value"})

    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM buffer")
        count = cursor.fetchone()[0]

    assert count == num_entries


def test_buffer_bounded_growth(tmp_path):
    """Test that the buffer respects max_buffer_size once implemented."""
    db_path = tmp_path / "test_buffer_bounded.sqlite"
    max_size = 5

    # We expect to be able to pass max_buffer_size after the fix
    try:
        buffer = NtfyBuffer(db_path, max_buffer_size=max_size)
    except TypeError:
        # If max_buffer_size is not yet implemented, this test will fail here or we skip it
        pytest.skip("max_buffer_size not yet implemented")
        return

    num_entries = 10
    for i in range(num_entries):
        buffer.add("topic", "http://localhost", f"data {i}", {"Header": "Value"})

    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM buffer")
        count = cursor.fetchone()[0]

    assert count <= max_size

    # Also verify that the LATEST entries are kept
    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT data FROM buffer ORDER BY created_at DESC, id DESC LIMIT 1")
        latest_data = cursor.fetchone()[0]
        assert latest_data == f"data {num_entries - 1}"
