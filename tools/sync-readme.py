#!/usr/bin/env python3
"""Fills the code blocks of README.md from the marked regions of the examples.

In an example:   // <snippet name> ... // </snippet>
In the README:   <!-- snippet: examples/NN-folder/File.cs#name --> ... <!-- /snippet -->
The text between the two README markers is replaced by the region, in a ```csharp block, with its common indent removed.

  python3 tools/sync-readme.py          rewrite README.md
  python3 tools/sync-readme.py --check  change nothing; exit 1 if README.md is out of date
"""
import re
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
MARKER = re.compile(r"<!-- snippet: (?P<path>[^#\s]+)#(?P<name>[\w-]+) -->\n.*?<!-- /snippet -->", re.S)


def region(path: str, name: str) -> str:
    text = (ROOT / path).read_text(encoding="utf-8")
    m = re.search(rf"^[ \t]*// <snippet {re.escape(name)}>\n(.*?)^[ \t]*// </snippet>", text, re.S | re.M)
    if not m:
        sys.exit(f"snippet '{name}' not found in {path}")
    return textwrap.dedent(m.group(1)).strip("\n")


def render(match: re.Match) -> str:
    code = region(match["path"], match["name"])
    return f"<!-- snippet: {match['path']}#{match['name']} -->\n```csharp\n{code}\n```\n<!-- /snippet -->"


def main() -> int:
    current = README.read_text(encoding="utf-8")
    updated = MARKER.sub(render, current)
    if "--check" in sys.argv:
        if updated != current:
            print("README.md is out of date with the examples; run tools/sync-readme.py")
            return 1
        print("README.md matches the examples")
        return 0
    README.write_text(updated, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
