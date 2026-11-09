#******************************************************************************
# SmartManipulator-X: Robot PC
#
# Description: Renders the Mermaid diagram sources (docs/**/diagrams/*.mmd) to
#              static SVG files (docs/**/images/<name>.svg) for the website and
#              the PDF manual. Run after changing a diagram:
#                  python tools/docs/render_mermaid.py
#
# Author:      Anton Vynohradov
# Email:       contact@systemfromscratch.com
# License:     Apache License 2.0
# Copyright (c) 2026 Anton Vynohradov
#
# SPDX-License-Identifier: Apache-2.0
#*****************************************************************************

"""Render Mermaid sources to plain SVG.

The PDF manual is rendered by WeasyPrint, which runs no JavaScript and draws no
<foreignObject>, so the diagrams are committed as SVG files with SVG text labels
(htmlLabels off). The page loads Mermaid from jsDelivr, so this needs a network
connection and Playwright with a Chromium browser (Windows: the installed Edge):

    python -m pip install playwright
    python -m playwright install chromium     # Linux only
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
MERMAID = "https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.min.js"
CONFIG = {
    "startOnLoad": False,
    "theme": "base",
    "htmlLabels": False,
    "flowchart": {"htmlLabels": False, "curve": "basis"},
    # wrap long messages so a sequence diagram fits the page width
    "sequence": {"wrap": True, "width": 150, "actorMargin": 30, "messageFontSize": 14,
                 "noteFontSize": 13, "actorFontSize": 14},
    "themeVariables": {
        "fontFamily": "Inter, 'Segoe UI', 'DejaVu Sans', Arial, sans-serif",
        "fontSize": "14px",
        "primaryColor": "#F2F5FA",
        "primaryBorderColor": "#1E5AA8",
        "primaryTextColor": "#0B2545",
        "lineColor": "#5A6472",
        "clusterBkg": "#FFFFFF",
        "clusterBorder": "#C9D3E0",
        "actorBkg": "#F2F5FA",
        "actorBorder": "#1E5AA8",
        "signalColor": "#0B2545",
        "noteBkgColor": "#FFF7EC",
    },
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--browser", default="auto", choices=["auto", "chromium", "msedge"])
    args = parser.parse_args()
    sources = sorted(ROOT.glob("docs/**/diagrams/*.mmd"))
    if not sources:
        print("no docs/**/diagrams/*.mmd sources")
        return 0

    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        channel = None if args.browser == "chromium" else "msedge"
        try:
            browser = pw.chromium.launch(channel=channel)
        except Exception:
            if args.browser != "auto":
                raise
            browser = pw.chromium.launch()
        page = browser.new_page()
        page.set_content(f'<html><body><script src="{MERMAID}"></script></body></html>')
        page.wait_for_function("window.mermaid !== undefined")
        page.evaluate(f"mermaid.initialize({json.dumps(CONFIG)})")
        for source in sources:
            svg = page.evaluate("async ([id, text]) => (await mermaid.render(id, text)).svg",
                                [source.stem.replace("-", "_"), source.read_text("utf-8")])
            target = source.parent.parent / "images" / f"{source.stem}.svg"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(svg + "\n", encoding="utf-8", newline="\n")
            print("wrote", target.relative_to(ROOT).as_posix())
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
