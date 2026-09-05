#!/usr/bin/env python3
"""Index local MicroDuck history read-only; keep extracted private text local."""
from collections import Counter
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3


def message(payload, record_type):
    if record_type == "response_item" and payload.get("type") == "message" and payload.get("role") in {"assistant", "user"}:
        role, phase, content = payload["role"], payload.get("phase", payload.get("channel", "")), payload.get("content", [])
    elif record_type == "event_msg" and payload.get("type") == "item_completed" and payload.get("item", {}).get("type") == "UserMessage":
        role, phase, content = "user", "", payload["item"].get("content", [])
    else:
        return None
    text = "\n".join(item.get("text", "") for item in content if isinstance(item, dict))
    if not text or "# AGENTS.md" in text or "<recommended_plugins>" in text:
        return None
    return {"role": role, "phase": phase, "text": text}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-home", type=Path, default=Path.home() / ".codex")
    parser.add_argument("--before", default=None, help="exclude tasks created on/after this UTC ISO date")
    parser.add_argument("--extra-thread", action="append", default=[], help="explicitly linked task missed by keyword discovery")
    parser.add_argument("--output", type=Path, required=True, help="new private local directory; never a tracked receipt folder")
    args = parser.parse_args()
    database = args.codex_home / "state_5.sqlite"
    connection = sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    rows = {r["id"]: dict(r) for r in connection.execute("SELECT id,rollout_path,cwd,created_at,archived FROM threads WHERE lower(cwd) LIKE '%microduck%' OR lower(title) LIKE '%microduck%' OR lower(title) LIKE '%robot duck%' OR lower(first_user_message) LIKE '%microduck%' OR lower(first_user_message) LIKE '%micro duck%'")}
    for thread_id in args.extra_thread:
        row = connection.execute("SELECT id,rollout_path,cwd,created_at,archived FROM threads WHERE id=?", (thread_id,)).fetchone()
        if row:
            rows[thread_id] = dict(row)
        else:
            parser.error(f"explicit task was not found: {thread_id}")
    connection.close()
    cutoff = datetime.fromisoformat(args.before).replace(tzinfo=timezone.utc).timestamp() if args.before else None
    args.output.mkdir(parents=True, exist_ok=False)
    index, errors = [], []
    with (args.output / "messages.jsonl").open("w") as messages:
        for row in sorted(rows.values(), key=lambda r: r["created_at"]):
            if cutoff is not None and row["created_at"] >= cutoff:
                continue
            path = Path(row["rollout_path"])
            try:
                digest, counts, seen, extracted, lines = hashlib.sha256(), Counter(), set(), 0, 0
                with path.open("rb") as source:
                    for lines, raw in enumerate(source, 1):
                        digest.update(raw)
                        try:
                            record = json.loads(raw)
                        except ValueError:
                            counts["malformed"] += 1
                            continue
                        counts[record.get("type", "unknown")] += 1
                        item = message(record.get("payload", {}), record.get("type"))
                        if item and item["text"] not in seen:
                            seen.add(item["text"])
                            extracted += 1
                            messages.write(json.dumps({"session": row["id"], "line": lines, **item}) + "\n")
                index.append({**row, "lines": lines, "sha256": digest.hexdigest(), "record_counts": dict(counts), "extracted_text_messages": extracted})
            except OSError as error:
                errors.append({"session": row["id"], "path": str(path), "error": str(error)})
    result = {"schema": "microduck.local-history-index/v1", "generated_at": datetime.now(timezone.utc).isoformat(),
              "before": args.before, "extra_threads": args.extra_thread, "sessions": index, "errors": errors,
              "boundary": "Keyword-discovered local history, not guaranteed coverage of deleted, unindexed or remote tasks. Private text stays in this output directory."}
    (args.output / "index.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"sessions": len(index), "lines": sum(r["lines"] for r in index), "messages": sum(r["extracted_text_messages"] for r in index), "errors": errors, "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
