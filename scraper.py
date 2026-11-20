"""Fetch a GitHub repository's primary language and star count into SQLite."""

import argparse
import sqlite3
import sys
from pathlib import Path

import requests

API_URL = "https://api.github.com/repos/{owner}/{repo}"
DEFAULT_REPOSITORY = "google/guava"
DEFAULT_DATABASE = Path(__file__).with_name("repositories.db")


def parse_repository(value: str) -> tuple[str, str]:
    """Validate and split an OWNER/REPO argument."""
    parts = value.strip("/").split("/")
    if len(parts) != 2 or not all(parts):
        raise argparse.ArgumentTypeError("repository must be in OWNER/REPO format")
    return parts[0], parts[1]


def fetch_repository(owner: str, repo: str) -> tuple[str, str, int]:
    """Return (full name, primary language, star count) from GitHub's API."""
    url = API_URL.format(owner=owner, repo=repo)
    try:
        response = requests.get(
            url,
            headers={"Accept": "application/vnd.github+json"},
            timeout=15,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"Could not fetch {owner}/{repo} from GitHub: {exc}") from exc

    try:
        data = response.json()
        full_name = data["full_name"]
        language = data.get("language") or "不明"
        stars = data["stargazers_count"]
    except (ValueError, KeyError, TypeError) as exc:
        raise RuntimeError("GitHub returned an unexpected repository response") from exc

    if not isinstance(stars, int):
        raise RuntimeError("GitHub returned an invalid star count")
    return full_name, language, stars


def save_repository(database: Path, name: str, language: str, stars: int) -> None:
    with sqlite3.connect(database) as connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS repositories (
                name TEXT PRIMARY KEY,
                language TEXT NOT NULL,
                stars INTEGER NOT NULL
            )"""
        )
        connection.execute(
            """INSERT INTO repositories (name, language, stars)
               VALUES (?, ?, ?)
               ON CONFLICT(name) DO UPDATE SET
                   language = excluded.language,
                   stars = excluded.stars""",
            (name, language, stars),
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Save a GitHub repository's primary language and star count."
    )
    parser.add_argument(
        "repository",
        nargs="?",
        default=DEFAULT_REPOSITORY,
        help=f"repository in OWNER/REPO format (default: {DEFAULT_REPOSITORY})",
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
        help=f"SQLite database path (default: {DEFAULT_DATABASE})",
    )
    args = parser.parse_args()

    try:
        owner, repo = parse_repository(args.repository)
        name, language, stars = fetch_repository(owner, repo)
        save_repository(args.database, name, language, stars)
    except (argparse.ArgumentTypeError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Repository: {name}")
    print(f"Language:   {language}")
    print(f"Stars:      {stars:,}")
    print(f"Saved to:   {args.database}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
