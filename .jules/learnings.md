# Learnings & FAQs

## Why do I get notifications with only "Triggered" in the body?
When using `ntfy_lite` as a logging handler, if the formatted message (like a large traceback) exceeds the server's body size limit (often 4096 bytes for `ntfy.sh`, but possibly smaller for self-hosted instances like `ntfy.hostux.net`), the server may convert the body text into a `.txt` file attachment. 

If this happens and there is no accompanying `Message` HTTP header, the `ntfy` server considers the text message empty and defaults the notification body to **"Triggered"**.

**Wait, what if even short messages say "Triggered"?**
If you pass a base URL with a trailing slash (e.g. `https://ntfy.hostux.net/`), the HTTP request resolves to a URL with a double-slash (e.g. `https://ntfy.hostux.net//topic`). Most proxies (Nginx) will respond with a `301 Moved Permanently` to redirect to the correct single-slash URL. During this `301` redirect, Python's `requests` library **drops the HTTP body**. The final request reaches the server with an empty body, resulting in "Triggered" once again! 

*(Note: `ntfy_lite` has now been updated to auto-strip trailing slashes from the base URL).*

## How to get truncated message in body AND full traceback in attachment?
Use the `AttachmentFormatter`. It handles large payloads by safely extracting a text preview (the top and bottom of the traceback) to send in the `Message` HTTP header, while putting the complete, un-truncated string into an attached `traceback.txt` file.

**Example loguru config:**
```python
import logging
from ntfy_lite import NtfyHandler
from ntfy_lite.formatter import AttachmentFormatter

ntfy = NtfyHandler(
    topic="your_topic",
    url="https://ntfy.sh",
    formatter=AttachmentFormatter()
)
```
