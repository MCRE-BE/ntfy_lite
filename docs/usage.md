---
hide:
  - navigation
---


# Usage

You may run these examples by running after installation:

- ntfy_lite_push_demo
- ntfy_lite_logging_demo

## CLI (Command Line Interface)

The package installs a command-line script called `ntfy-lite`, making it easy to push notifications directly from your shell:

``` bash
ntfy-lite "my_topic" "Hello!" -m "This is a CLI test" -p high -t warning,skull
```

You can view all available options via the help menu:

``` bash
ntfy-lite --help
```

## pushing notifications

``` py
--8<-- "ntfy_lite/demo_push.py"
```

## logging handler

``` py
--8<-- "ntfy_lite/demo_logging.py"
```

### Handling Long Tracebacks

By default, `ntfy_lite` truncates long log messages (like stack traces) to fit the server's body limit. If you want a preview of the error in the notification body **and** the full traceback attached as a `.txt` file, use the `AttachmentFormatter`:

```python
import logging
from ntfy_lite import NtfyHandler
from ntfy_lite.formatter import AttachmentFormatter

# Pass the AttachmentFormatter to your handler
ntfy_handler = NtfyHandler(
    topic="my_topic",
    formatter=AttachmentFormatter()
)

logging.basicConfig(handlers=[ntfy_handler])
logging.error("Something broke!", exc_info=True)
```
