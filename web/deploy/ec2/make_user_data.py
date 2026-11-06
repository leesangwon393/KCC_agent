#!/usr/bin/env python3
"""Bundle the current static site into EC2 user data for Amazon Linux 2023."""

from __future__ import annotations

import argparse
import base64
import io
from pathlib import Path
import tarfile


LIMIT = 16 * 1024
ROOT = Path(__file__).resolve().parents[2]


def build() -> bytes:
    site = ROOT / "dist"
    files = sorted(path for path in site.iterdir() if path.is_file())
    if not any(path.name == "index.html" for path in files):
        raise SystemExit("dist/index.html is missing")

    archive = io.BytesIO()
    with tarfile.open(fileobj=archive, mode="w:gz") as bundle:
        for path in files:
            bundle.add(path, arcname=path.name, recursive=False)

    payload = base64.b64encode(archive.getvalue()).decode("ascii")
    script = f"""#!/bin/bash
set -euo pipefail
dnf install -y nginx
mkdir -p /usr/share/nginx/html
base64 -d <<'SITE_BUNDLE' | tar -xz -C /usr/share/nginx/html
{payload}
SITE_BUNDLE
cat > /etc/nginx/nginx.conf <<'NGINX_CONF'
user nginx;
worker_processes auto;
pid /run/nginx.pid;
events {{ worker_connections 1024; }}
http {{
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    sendfile on;
    server {{
        listen 80 default_server;
        server_name _;
        root /usr/share/nginx/html;
        index index.html;
        location / {{ try_files $uri $uri/ /index.html; }}
        add_header X-Content-Type-Options nosniff always;
        add_header Referrer-Policy strict-origin-when-cross-origin always;
    }}
}}
NGINX_CONF
nginx -t
systemctl enable --now nginx
""".encode("utf-8")
    if len(script) > LIMIT:
        raise SystemExit(f"EC2 user data is {len(script)} bytes; limit is {LIMIT}")
    return script


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path, help="output shell script for EC2 user data")
    args = parser.parse_args()
    script = build()
    args.output.write_bytes(script)
    print(f"Wrote {args.output} ({len(script)} bytes)")


if __name__ == "__main__":
    main()
