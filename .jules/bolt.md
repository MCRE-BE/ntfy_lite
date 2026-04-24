# Performance Learnings

- **Database Batching**: In `ntfy_lite/buffer.py`, replacing the N+1 repeated opening of an SQLite database connection and delete operation inside the retry loop with an ID collection and a batched `executemany` database delete reduced execution time drastically (from ~2.09s to ~0.02s for 1000 items). Accumulating successful/failed IDs is much safer than holding an open SQLite transaction outside the loop (which would lock the DB across minutes of sleep time).
