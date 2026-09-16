"""Generate the static map configuration from a Cloudflare Pages environment variable."""

import os
from pathlib import Path


base_url = os.environ.get("R2_BASE_URL", "").strip().rstrip("/")
if not base_url:
    raise SystemExit("R2_BASE_URL must be configured in Cloudflare Pages environment variables")

Path(__file__).with_name("config.js").write_text(
    "window.SA_GBV_CONFIG = {\n"
    f'  R2_BASE_URL: {base_url!r}\n'
    "};\n",
    encoding="utf-8",
)
print("Generated web/config.js from R2_BASE_URL")
