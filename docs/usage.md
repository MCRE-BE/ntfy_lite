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

