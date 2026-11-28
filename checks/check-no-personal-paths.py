"""Scan the working copies of Git-tracked files, not untracked local files."""

import argparse
import os
from pathlib import Path
import re
import stat
import sys

from mechanical_common import CheckError, git, sensitive


HOME_PATH = re.compile(rb"/(?:home|Users)/[^/\x00\n]+/")


def first_match(project, relative):
    path = project / relative
    parent = project
    for part in Path(relative).parts[:-1]:
        parent /= part
        if parent.is_symlink():
            raise CheckError("cannot scan through a symlinked parent directory")
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        return None
    if stat.S_ISLNK(mode):
        # Inspect only link text, never its destination.
        return 1 if HOME_PATH.search(os.fsencode(os.readlink(path))) else None
    if not stat.S_ISREG(mode):
        raise CheckError("expected a regular file or symlink")
    with path.open("rb") as source:
        for number, line in enumerate(source, 1):
            if HOME_PATH.search(line):
                return number
    return None


def check(project):
    root = Path(os.fsdecode(git(project, "rev-parse", "--show-toplevel").rstrip(b"\n")))
    tracked = git(root, "ls-files", "--stage", "-z").split(b"\0")
    failed = False
    seen = set()
    for entry in filter(None, tracked):
        metadata, raw_path = entry.split(b"\t", 1)
        if raw_path in seen:
            continue
        seen.add(raw_path)
        relative = os.fsdecode(raw_path)
        if sensitive(relative):
            print("check-no-personal-paths: sensitive tracked path (not read)", file=sys.stderr)
            failed = True
            continue
        if metadata.startswith(b"160000 "):  # A submodule is not a tracked file.
            continue
        try:
            line = first_match(root, relative)
            if line is not None:
                print(f"{ascii(relative)}:{line}: absolute home path", file=sys.stderr)
                failed = True
        except (CheckError, OSError) as exc:
            detail = str(exc) if isinstance(exc, CheckError) else "could not read tracked path"
            print(f"{ascii(relative)}: {detail}", file=sys.stderr)
            failed = True
    if not failed:
        print("check-no-personal-paths: OK")
    return int(failed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    args = parser.parse_args()
    try:
        return check(args.repo)
    except CheckError as exc:
        print(f"check-no-personal-paths: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
