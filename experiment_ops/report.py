"""Portable report; embedded data is escaped and never interpreted as HTML."""
import json
from pathlib import Path


def render(result):
    payload = json.dumps(result, ensure_ascii=True, allow_nan=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    template = Path(__file__).with_name("report.html").read_text()
    template = template.replace("__REPORT_SCRIPT__", Path(__file__).with_name("report.js").read_text(), 1)
    return template.replace("__COMPARISON_DATA__", payload, 1)
