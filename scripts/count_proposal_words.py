#!/usr/bin/env python3
"""Count the words of the proposal answers (class="answer"), excluding question titles, footer and SVG.

Usage: python3 scripts/count_proposal_words.py [docs/proposal/proposal.html]
Also reports the whole-page count. Exits 1 when either exceeds 500.
"""

from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path

LIMIT = 500
DEFAULT = Path(__file__).resolve().parent.parent / "docs" / "proposal" / "proposal.html"


class AnswerParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.depth = 0  # >0 while inside an answer element
        self.answers: list[list[str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        classes = (dict(attrs).get("class") or "").split()
        if self.depth:
            self.depth += 1
        elif "answer" in classes:
            self.depth = 1
            self.answers.append([])

    def handle_endtag(self, tag: str) -> None:
        if self.depth:
            self.depth -= 1

    def handle_data(self, data: str) -> None:
        if self.depth:
            self.answers[-1].append(data)


def count(html: str) -> list[int]:
    parser = AnswerParser()
    parser.feed(html)
    return [len(" ".join(parts).replace("→", " ").split()) for parts in parser.answers]


def whole_page(html: str) -> int:
    """Words of all visible body text (headings, answers, SVG labels, footer, signature line)."""
    import re
    from html import unescape

    body = html[html.index("<body>"):]
    text = unescape(re.sub(r"<[^>]+>", " ", body)).replace("\u2192", " ")
    return len(text.split())


def main(argv: list[str]) -> int:
    path = Path(argv[1]) if len(argv) > 1 else DEFAULT
    counts = count(path.read_text(encoding="utf-8"))
    for i, n in enumerate(counts, 1):
        print(f"{i:>2}: {n}")
    total = sum(counts)
    whole = whole_page(path.read_text(encoding="utf-8"))
    print(f"answers: {len(counts)}  total words: {total} (limit {LIMIT})")
    print(f"whole page (headings, SVG, footer, signature line): {whole} (limit {LIMIT})")
    return 0 if len(counts) == 10 and total <= LIMIT and whole <= LIMIT else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
