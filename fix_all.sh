#!/bin/bash

# 1. fix .ruff.toml
cat << 'PYEOF' > fix_ruff.py
with open(".ruff.toml", "r") as f:
    content = f.read()

import re
content = re.sub(r'\s*# todo : fix later.*?(\n\])', r'\1', content, flags=re.DOTALL, count=1)

test_ignores = '"**/tests/*" = [\n'
test_ignores_new = test_ignores + '    "D100",\n    "D103",\n    "D104",\n    "ANN401",\n    "ANN002",\n    "ANN003",\n    "FBT001",\n    "FBT002",\n'

content = content.replace(test_ignores, test_ignores_new)

with open(".ruff.toml", "w") as f:
    f.write(content)
PYEOF
python3 fix_ruff.py

# 2. fix ntfy_lite/actions.py
cat << 'PYEOF' > fix_actions.py
import re

with open("ntfy_lite/actions.py", "r") as f:
    content = f.read()

content = content.replace("url: str,\n        clear: bool = False", "url: str,\n        *,\n        clear: bool = False")

with open("ntfy_lite/actions.py", "w") as f:
    f.write(content)
PYEOF
python3 fix_actions.py

# 3. fix ntfy_lite/formatter.py
cat << 'PYEOF' > fix_formatter.py
with open("ntfy_lite/formatter.py", "r") as f:
    content = f.read()

content = content.replace("key: typing.Any", "key: str")
content = content.replace("def process(\n        self: Self,\n        message: str,\n    ) -> FormatterPayload:", "def process(\n        self: Self,\n        message: str,\n    ) -> FormatterPayload:\n        \"\"\"Process the message string and return properties for the DataPayload.\"\"\"")
content = content.replace("default: typing.Any = None,", "default: object = None,  # noqa: ANN401")
content = content.replace(") -> typing.Any:", ") -> typing.Any:  # noqa: ANN401")
content = content.replace("value: typing.Any = None,", "value: object = None,  # noqa: ANN401")

with open("ntfy_lite/formatter.py", "w") as f:
    f.write(content)
PYEOF
python3 fix_formatter.py

# 4. fix ntfy_lite/handler.py
cat << 'PYEOF' > fix_handler.py
with open("ntfy_lite/handler.py", "r") as f:
    content = f.read()

content = content.replace("url: str = \"https://ntfy.sh\",\n        twice_in_a_row: bool = True,", "url: str = \"https://ntfy.sh\",\n        *,\n        twice_in_a_row: bool = True,")

with open("ntfy_lite/handler.py", "w") as f:
    f.write(content)
PYEOF
python3 fix_handler.py

# 5. fix ntfy_lite/ntfy.py
cat << 'PYEOF' > fix_ntfy.py
with open("ntfy_lite/ntfy.py", "r") as f:
    content = f.read()

content = content.replace("_,", "_: object,")
content = content.replace("__,", "__: object,")
content = content.replace("___,", "___: object,")
content = content.replace("message: typing.Any | None,", "message: object | None,")
content = content.replace("payload_data: typing.Any,", "payload_data: typing.IO[typing.Any] | str,")
content = content.replace("message: typing.Any | None = None,", "message: object | None = None,")

with open("ntfy_lite/ntfy.py", "w") as f:
    f.write(content)
PYEOF
python3 fix_ntfy.py

# 6. fix ntfy_lite/version.py
cat << 'PYEOF' > fix_version.py
with open("ntfy_lite/version.py", "r") as f:
    content = f.read()

with open("ntfy_lite/version.py", "w") as f:
    f.write('"""Module defining the version."""\n\n' + content)
PYEOF
python3 fix_version.py

# 7. fix tests/test_ntfy_lite.py
cat << 'PYEOF' > fix_test_ntfy_lite.py
with open("tests/test_ntfy_lite.py", "r") as f:
    content = f.read()

content = content.replace("def mock_put(*args, **kwargs):", "def mock_put(*args: object, **kwargs: object) -> MockResponse:")
content = content.replace("def mock_put(*args: typing.Any, **kwargs: typing.Any) -> MockResponse:", "def mock_put(*args: object, **kwargs: object) -> MockResponse:")
content = content.replace("def mock_put(*args: typing.Any, **kwargs) -> MockResponse:", "def mock_put(*args: object, **kwargs: object) -> MockResponse:")

with open("tests/test_ntfy_lite.py", "w") as f:
    f.write(content)
PYEOF
python3 fix_test_ntfy_lite.py

rm fix_*.py
