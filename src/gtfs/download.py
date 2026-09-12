"""
TransitPulse GTFS static feed downloader.

Downloads the official MTA NYC Subway GTFS static feed and extracts it
into a local directory for analytics/reference data.
"""

from __future__ import annotations

import os
import zipfile
from pathlib import Path

import requests


DEFAULT_GTFS_URL = (
    "https://rrgtfsfeeds.s3.amazonaws.com/gtfs_subway.zip"
)


def download_gtfs(
    output_dir: str | Path = "data/gtfs",
    feed_url: str | None = None,
    timeout_seconds: int = 60,
) -> Path:
    """
    Download and extract the MTA NYC Subway GTFS static feed.

    Returns:
        Path to the extracted GTFS directory.
    """

    url = (
        feed_url
        or os.environ.get("GTFS_STATIC_URL")
        or DEFAULT_GTFS_URL
    )

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    zip_path = output_path / "gtfs_subway.zip"

    response = requests.get(
        url,
        timeout=timeout_seconds,
    )
    response.raise_for_status()

    zip_path.write_bytes(response.content)

    with zipfile.ZipFile(zip_path, "r") as archive:
        archive.extractall(output_path)

    return output_path


if __name__ == "__main__":
    path = download_gtfs()
    print(f"GTFS feed extracted to: {path}")
