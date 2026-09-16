"""Upload generated data artifacts to Cloudflare R2 using its S3 API."""

import argparse
import mimetypes
import os
from pathlib import Path


CONTENT_TYPES = {
    ".csv": "text/csv",
    ".json": "application/json",
    ".parquet": "application/vnd.apache.parquet",
    ".pmtiles": "application/vnd.pmtiles",
}


def upload_tree(
    root: Path,
    *,
    bucket: str,
    endpoint_url: str,
    prefix: str = "latest",
) -> int:
    """Upload every file below ``root``, replacing the same R2 key."""
    try:
        import boto3
        from botocore.config import Config
    except ImportError as error:
        raise ImportError("Install R2 publishing support with `pip install -e .`") from error

    client = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        region_name="auto",
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
        ),
    )
    uploaded = 0
    for path in sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and not any(part.startswith(".") for part in path.relative_to(root).parts)
    ):
        key = "/".join(part for part in (prefix.strip("/"), path.relative_to(root).as_posix()) if part)
        content_type = CONTENT_TYPES.get(path.suffix.lower()) or mimetypes.guess_type(path.name)[0]
        extra_args = {"CacheControl": "no-cache"}
        if content_type:
            extra_args["ContentType"] = content_type
        client.upload_file(str(path), bucket, key, ExtraArgs=extra_args)
        uploaded += 1
        print(f"uploaded s3://{bucket}/{key}")
    return uploaded


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("data"))
    parser.add_argument("--bucket", default=os.environ.get("R2_BUCKET"))
    parser.add_argument("--endpoint-url", default=os.environ.get("R2_ENDPOINT_URL"))
    parser.add_argument("--prefix", default="latest")
    args = parser.parse_args()
    if not args.bucket or not args.endpoint_url:
        parser.error("R2_BUCKET and R2_ENDPOINT_URL are required")
    upload_tree(args.root, bucket=args.bucket, endpoint_url=args.endpoint_url, prefix=args.prefix)


if __name__ == "__main__":
    main()