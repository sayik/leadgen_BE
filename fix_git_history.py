import json
import random
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo


GIT_NAME = "sayi"
GIT_EMAIL = "sayikrishnapk@gmail.com"

TIMEZONE = ZoneInfo("Asia/Kolkata")

START = datetime(2026, 4, 9, 0, 0, 0, tzinfo=TIMEZONE)
END = datetime(2026, 4, 20, 23, 59, 59, tzinfo=TIMEZONE)


def git(*args, check=True):
    return subprocess.run(
        ["git", *args],
        check=check,
        capture_output=True,
        text=True,
    )


def main():
    repo = Path(git("rev-parse", "--show-toplevel").stdout.strip())

    # Never rewrite a repository with uncommitted changes.
    status = git("status", "--porcelain").stdout

    if status:
        raise RuntimeError("Working tree is not clean. Commit or stash your changes first.")

    # Check git-filter-repo installation.
    git("filter-repo", "--version")

    # Get all commits in parent-before-child topological order.
    commits = git(
        "rev-list",
        "--reverse",
        "--topo-order",
        "--all",
    ).stdout.splitlines()

    if not commits:
        raise RuntimeError("No commits found.")

    print(f"Found {len(commits)} commits.")

    # Create a backup outside the repository.
    backup = repo.parent / (f"{repo.name}-before-history-fix.bundle")

    git("bundle", "create", str(backup), "--all")

    print(f"Backup created: {backup}")

    # Generate unique random timestamps.
    total_seconds = int((END - START).total_seconds())

    random_offsets = sorted(
        random.sample(
            range(total_seconds + 1),
            len(commits),
        )
    )

    date_mapping = {}

    for commit_hash, offset in zip(commits, random_offsets):
        timestamp = START + timedelta(seconds=offset)

        unix_timestamp = int(timestamp.timestamp())

        # Git's internal date format.
        date_mapping[commit_hash] = f"{unix_timestamp} +0530"

    # Save the mapping temporarily.
    mapping_file = repo.parent / "leadgen_commit_dates.json"

    mapping_file.write_text(
        json.dumps(date_mapping),
        encoding="utf-8",
    )

    # Callback executed for every commit by git-filter-repo.
    callback = f"""
import json

with open({str(mapping_file)!r}, encoding="utf-8") as f:
    _dates = json.load(f)

_date = _dates[commit.original_id.decode("ascii")]

commit.author_name = b"{GIT_NAME}"
commit.author_email = b"{GIT_EMAIL}"

commit.committer_name = b"{GIT_NAME}"
commit.committer_email = b"{GIT_EMAIL}"

commit.author_date = _date.encode("ascii")
commit.committer_date = _date.encode("ascii")
"""

    try:
        print("Rewriting commit history...")

        git(
            "filter-repo",
            "--force",
            "--commit-callback",
            callback,
        )

    finally:
        mapping_file.unlink(missing_ok=True)

    print("\nHistory successfully rewritten.")
    print("\nUpdated commits:")

    result = git(
        "log",
        "--format=%h | %an <%ae> | %ad",
        "--date=iso",
        "--all",
    )

    print(result.stdout)

    print(f"\nBackup: {backup}")


if __name__ == "__main__":
    main()
