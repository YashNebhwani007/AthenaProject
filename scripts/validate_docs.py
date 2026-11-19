"""Documentation markdown link and reference validation script."""

from __future__ import annotations

import re
import sys
from pathlib import Path


def validate_markdown_links(root: Path) -> int:
    """Verify all markdown links across docs/ and README.md resolve to existing files."""
    md_files = list((root / "docs").rglob("*.md"))
    readme = root / "README.md"
    if readme.exists():
        md_files.append(readme)

    link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    errors = 0
    checked = 0

    for md in md_files:
        content = md.read_text(encoding="utf-8")
        for match in link_pattern.finditer(content):
            url = match.group(2)
            # Skip web URLs, mailto, and anchor jumps
            if url.startswith(("http://", "https://", "mailto:", "#")):
                continue

            target_path = url.split("#")[0]
            if not target_path:
                continue

            resolved = (md.parent / target_path).resolve()
            checked += 1
            if not resolved.exists():
                sys.stderr.write(f"BROKEN LINK in {md.relative_to(root)}: {url}\n")
                errors += 1

    print(f"Validated {checked} markdown links across {len(md_files)} files. Errors: {errors}")
    return 0 if errors == 0 else 1


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    code = validate_markdown_links(root)
    sys.exit(code)


if __name__ == "__main__":
    main()
