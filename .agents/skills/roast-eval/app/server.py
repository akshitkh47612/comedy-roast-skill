#!/usr/bin/env python3
"""Stdlib-only review server for roast-eval. No dependencies."""

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
DATA_FILE = APP_DIR.parent / "data" / "bits.jsonl"
INDEX_FILE = APP_DIR / "index.html"
VALID_LABELS = {"Pass", "Fail", "TooFar"}


def read_bits() -> list[dict]:
    if not DATA_FILE.exists():
        return []
    bits = []
    with DATA_FILE.open("r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                bits.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"skipping malformed line {line_num} in {DATA_FILE}", file=sys.stderr)
    return bits


def write_bits(bits: list[dict]) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp_file = DATA_FILE.with_suffix(".jsonl.tmp")
    with tmp_file.open("w", encoding="utf-8") as f:
        for bit in bits:
            f.write(json.dumps(bit, ensure_ascii=False) + "\n")
    tmp_file.replace(DATA_FILE)


def append_bits(new_items: list[dict]) -> list[dict]:
    existing = read_bits()
    now = datetime.now(timezone.utc).isoformat()
    appended = [
        {
            "id": item.get("id") or f"b_{uuid.uuid4().hex[:8]}",
            "roast_id": item.get("roast_id", "unknown"),
            "timestamp": item.get("timestamp", now),
            "section": item.get("section", "Unsorted"),
            "text": item["text"],
            "source_refs": item.get("source_refs", []),
            "label": item.get("label"),
            "note": item.get("note", ""),
        }
        for item in new_items
    ]
    write_bits(existing + appended)
    return appended


def update_rating(bit_id: str, label: str | None, note: str) -> dict | None:
    if label is not None and label not in VALID_LABELS:
        raise ValueError(f"invalid label {label!r}, expected one of {VALID_LABELS}")
    bits = read_bits()
    updated = None
    result = []
    for bit in bits:
        if bit.get("id") == bit_id:
            updated = {**bit, "label": label, "note": note}
            result.append(updated)
        else:
            result.append(bit)
    if updated is not None:
        write_bits(result)
    return updated


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, payload) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, status: int, html: str) -> None:
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return None
        raw = self.rfile.read(length)
        return json.loads(raw)

    def do_GET(self) -> None:  # noqa: N802 (stdlib method name)
        if self.path in ("/", "/index.html"):
            if not INDEX_FILE.exists():
                self._send_json(500, {"error": "index.html missing"})
                return
            self._send_html(200, INDEX_FILE.read_text(encoding="utf-8"))
        elif self.path == "/api/bits":
            self._send_json(200, read_bits())
        else:
            self._send_json(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        try:
            payload = self._read_json_body()
        except json.JSONDecodeError:
            self._send_json(400, {"error": "invalid JSON body"})
            return

        if self.path == "/api/bits":
            items = payload if isinstance(payload, list) else [payload]
            try:
                appended = append_bits(items)
            except KeyError as exc:
                self._send_json(400, {"error": f"missing required field {exc}"})
                return
            self._send_json(200, appended)
        elif self.path == "/api/ratings":
            if not isinstance(payload, dict) or "id" not in payload:
                self._send_json(400, {"error": "expected {id, label, note}"})
                return
            try:
                updated = update_rating(
                    payload["id"], payload.get("label"), payload.get("note", "")
                )
            except ValueError as exc:
                self._send_json(400, {"error": str(exc)})
                return
            if updated is None:
                self._send_json(404, {"error": f"no bit with id {payload['id']!r}"})
                return
            self._send_json(200, updated)
        else:
            self._send_json(404, {"error": "not found"})

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write(f"[roast-eval-app] {fmt % args}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8420)
    args = parser.parse_args()

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"roast-eval review app: http://127.0.0.1:{args.port}")
    print(f"reading/writing: {DATA_FILE}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
