#!/usr/bin/env python3
"""Tiny HTTP server that supports Range requests for Kodi repo hosting."""

from __future__ import annotations

import argparse
import os
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional, Tuple


class RangeRequestHandler(SimpleHTTPRequestHandler):
    """SimpleHTTPRequestHandler with HTTP Range support for files."""

    range_header: Optional[Tuple[int, int]]

    def __init__(self, *args, directory: str, **kwargs) -> None:
        self.range_header = None
        super().__init__(*args, directory=directory, **kwargs)

    def send_head(self):
        """Handle GET/HEAD with optional Range header."""
        if self.command not in ("GET", "HEAD"):
            return super().send_head()

        path = self.translate_path(self.path)
        if os.path.isdir(path):
            return super().send_head()

        try:
            f = open(path, "rb")
        except OSError:
            self.send_error(404, "File not found")
            return None

        file_stat = os.fstat(f.fileno())
        file_len = file_stat.st_size
        ctype = self.guess_type(path)

        range_header = self.headers.get("Range")
        if not range_header:
            self.range_header = None
            self.send_response(200)
            self.send_header("Content-type", ctype)
            self.send_header("Content-Length", str(file_len))
            self.send_header("Accept-Ranges", "bytes")
            self.end_headers()
            return f

        start, end = self._parse_range(range_header, file_len)
        if start is None:
            self.send_error(416, "Requested Range Not Satisfiable")
            f.close()
            return None

        self.range_header = (start, end)
        self.send_response(206)
        self.send_header("Content-type", ctype)
        self.send_header("Content-Range", f"bytes {start}-{end}/{file_len}")
        self.send_header("Content-Length", str(end - start + 1))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        f.seek(start)
        return f

    def copyfile(self, source, outputfile):
        """Write only requested range when applicable."""
        if self.range_header is None:
            super().copyfile(source, outputfile)
            return

        start, end = self.range_header
        remaining = end - start + 1
        bufsize = 64 * 1024
        while remaining > 0:
            chunk = source.read(min(bufsize, remaining))
            if not chunk:
                break
            outputfile.write(chunk)
            remaining -= len(chunk)

    @staticmethod
    def _parse_range(header: str, file_len: int) -> Tuple[Optional[int], Optional[int]]:
        if not header.startswith("bytes="):
            return (None, None)
        try:
            start_str, end_str = header.split("=", 1)[1].split("-", 1)
            start = int(start_str) if start_str else 0
            end = int(end_str) if end_str else file_len - 1
        except Exception:
            return (None, None)

        if start < 0 or end < start or end >= file_len:
            return (None, None)
        return (start, end)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve repo assets with Range support.")
    parser.add_argument(
        "--host", default="0.0.0.0", help="Interface to bind (default: %(default)s)"
    )
    parser.add_argument(
        "--port", type=int, default=8080, help="Port to listen on (default: %(default)s)"
    )
    parser.add_argument(
        "--directory",
        default=".",
        help="Directory to serve (default: current working directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    handler = partial(RangeRequestHandler, directory=os.path.abspath(args.directory))
    with ThreadingHTTPServer((args.host, args.port), handler) as httpd:
        print(f"Serving {args.directory} at http://{args.host}:{args.port}/")
        httpd.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
