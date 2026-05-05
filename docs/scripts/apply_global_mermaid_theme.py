"""Inject a global Mermaid init block in all Markdown Mermaid fences.

This is a build-time workaround for MyST builds where Mermaid theme
configuration cannot be set once globally from ``myst.yml``.
"""

from __future__ import annotations

from pathlib import Path
import re


MERMAID_INIT = (
    '%%{init: {"theme":"base","themeVariables":{"primaryColor":"#f6f3ee",'
    '"primaryTextColor":"#222222","primaryBorderColor":"#555555",'
    '"lineColor":"#666666","secondaryColor":"#e9ecef","tertiaryColor":"#ffffff",'
    '"fontFamily":"Inter, Arial, sans-serif"},"flowchart":{"curve":"basis"},'
    '"deterministicIds":true}}%%'
)

FENCE_START_RE = re.compile(r"^```(?:\{mermaid\}|mermaid)\s*$")
FENCE_END_RE = re.compile(r"^```\s*$")
INIT_LINE_RE = re.compile(r"^\s*%%\{init:.*\}%%\s*$")


def _inject_mermaid_init(markdown_text: str) -> tuple[str, bool]:
    newline = "\r\n" if "\r\n" in markdown_text else "\n"
    lines = markdown_text.splitlines(keepends=True)
    output: list[str] = []
    changed = False
    i = 0

    while i < len(lines):
        stripped = lines[i].rstrip("\r\n")
        if not FENCE_START_RE.match(stripped):
            output.append(lines[i])
            i += 1
            continue

        # Keep opening fence as-is.
        output.append(lines[i])
        i += 1

        body: list[str] = []
        while i < len(lines):
            current = lines[i]
            if FENCE_END_RE.match(current.rstrip("\r\n")):
                break
            body.append(current)
            i += 1

        # Unclosed fence: keep untouched.
        if i >= len(lines):
            output.extend(body)
            break

        new_body = _normalize_mermaid_block(body, newline)
        if new_body != body:
            changed = True
        output.extend(new_body)

        # Closing fence.
        output.append(lines[i])
        i += 1

    return "".join(output), changed


def _normalize_mermaid_block(body: list[str], newline: str) -> list[str]:
    if not body:
        return [MERMAID_INIT + newline]

    # In directive fences (```{mermaid}), directive options can be at the top.
    insert_at = 0
    while insert_at < len(body) and body[insert_at].lstrip().startswith(":"):
        insert_at += 1
    if insert_at < len(body) and body[insert_at].strip() == "":
        insert_at += 1

    first_content = insert_at
    while first_content < len(body) and body[first_content].strip() == "":
        first_content += 1

    new_body = body.copy()
    if first_content < len(new_body) and INIT_LINE_RE.match(
        new_body[first_content].rstrip("\r\n")
    ):
        new_body[first_content] = MERMAID_INIT + newline
        return new_body

    new_body.insert(insert_at, MERMAID_INIT + newline)
    return new_body


def main() -> None:
    docs_root = Path("docs")
    updated = 0
    scanned = 0

    for md_path in docs_root.rglob("*.md"):
        if "_build" in md_path.parts:
            continue

        scanned += 1
        original = md_path.read_text(encoding="utf-8")
        rewritten, changed = _inject_mermaid_init(original)
        if changed:
            md_path.write_text(rewritten, encoding="utf-8")
            updated += 1

    print(f"Mermaid theme injection: {updated} file(s) updated over {scanned} scanned.")


if __name__ == "__main__":
    main()
