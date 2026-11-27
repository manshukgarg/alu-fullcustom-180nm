#!/usr/bin/env python3
"""Page numbers for the contents and lists of the report.

  python3 docs/report/find_pages.py ALU_project_report.pdf

Reads find.json (written by build_report.js: entry -> text at the start of a line) and the PDF
text (pdftotext -layout), and writes pages.json (entry -> page number as printed: roman for the
front matter, arabic from Chapter 1 on).
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def roman(n):
    out = ""
    for v, s in ((10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")):
        while n >= v:
            out += s
            n -= v
    return out


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


def main(pdf):
    text = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True, check=True).stdout
    pages = [[norm(l) for l in p.splitlines() if l.strip()] for p in text.split("\f")]
    find = json.load(open(os.path.join(HERE, "find.json")))
    body0 = next(i for i, p in enumerate(pages) if "CHAPTER 1" in p)
    front0 = 1                                   # page after the title page
    out, missing = {}, []
    for key, s in find.items():
        s = norm(s)
        front = key.startswith("front:")
        rng = range(front0, body0) if front else range(body0, len(pages))
        exact = key.startswith(("ch:", "front:")) or key == "refs"
        hit = None
        for i in rng:
            if any((l == s) if exact else l.startswith(s) for l in pages[i]):
                hit = i
                break
        if hit is None:
            missing.append(key)
            continue
        out[key] = roman(hit - front0 + 1) if front else str(hit - body0 + 1)
    json.dump(out, open(os.path.join(HERE, "pages.json"), "w"), indent=1)
    print(f"pages.json: {len(out)} entries; body starts on PDF page {body0 + 1}; {len(pages) - 1} pages")
    if missing:
        print("not found:", ", ".join(missing))
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "ALU_project_report.pdf"))
