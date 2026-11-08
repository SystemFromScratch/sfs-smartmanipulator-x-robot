"""MkDocs hook of the SmartManipulator-X documentation.

Turns an image that stands alone on its line, the usual Markdown form

    ![Caption text](images/picture.png)

into a captioned figure (rendered with the md_in_html extension):

    <figure class="smx-figure"><img ...><figcaption>Caption text</figcaption></figure>

The Markdown files stay plain, so they also render on GitHub. tools/docs/build_manual.py
imports `figures()` so that the PDF manual gets the same captions.
"""

from __future__ import annotations

import html
import re

_IMAGE_LINE = re.compile(r"^!\[(?P<alt>[^\]]+)\]\((?P<src>[^)\s]+)\)[ \t]*$", re.MULTILINE)
_FENCE = re.compile(r"^(```|~~~).*?^\1[ \t]*$", re.MULTILINE | re.DOTALL)


def figures(markdown: str) -> str:
    """Wrap every stand-alone image outside fenced code in a captioned figure."""

    def to_figure(match: re.Match) -> str:
        alt, src = match.group("alt"), match.group("src")
        caption = html.escape(alt, quote=False)
        return (
            '<figure class="smx-figure" markdown="1">\n\n'
            f"![{alt}]({src})\n\n"
            f"<figcaption>{caption}</figcaption>\n"
            "</figure>"
        )

    parts, last = [], 0
    for fence in _FENCE.finditer(markdown):
        parts.append(_IMAGE_LINE.sub(to_figure, markdown[last:fence.start()]))
        parts.append(fence.group(0))
        last = fence.end()
    parts.append(_IMAGE_LINE.sub(to_figure, markdown[last:]))
    return "".join(parts)


def on_page_markdown(markdown: str, **kwargs) -> str:
    return figures(markdown)
