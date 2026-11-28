"""Verify a consumer's cstack installation against a tagged local Git source."""

import argparse
import json
import os
from pathlib import Path
import re
import stat
import sys

from mechanical_common import CheckError, git, sensitive


LOCK = ".opencode/cstack.lock.json"
TAG = re.compile(r"v[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.+-]+)?")
SKILL_ID = re.compile(r"[a-z0-9][a-z0-9-]{0,63}")
FILE_MODES = {b"100644", b"100755"}


def mode(path):
    try:
        return path.lstat().st_mode
    except FileNotFoundError:
        return 0


def read_pin(project, source):
    if not stat.S_ISDIR(mode(project / ".opencode")) or not stat.S_ISREG(mode(project / LOCK)):
        raise CheckError(f"{LOCK}: expected a regular lock file under a real .opencode directory")

    def unique_fields(pairs):
        fields = dict(pairs)
        if len(fields) != len(pairs):
            raise ValueError("duplicate field")
        return fields

    try:
        lock = json.loads((project / LOCK).read_bytes(), object_pairs_hook=unique_fields)
    except (ValueError, RecursionError):
        raise CheckError(f"{LOCK}: invalid JSON lock") from None
    if not isinstance(lock, dict) or lock.keys() != {"version", "tag", "commit"}:
        raise CheckError(f"{LOCK}: expected version, tag and commit")
    tag, commit = lock["tag"], lock["commit"]
    if not isinstance(tag, str) or len(tag) > 64 or not TAG.fullmatch(tag):
        raise CheckError(f"{LOCK}: invalid tag")
    if lock["version"] != tag[1:]:
        raise CheckError(f"{LOCK}: version does not match tag")
    try:
        resolved = git(source, "rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}")
    except CheckError:
        raise CheckError(f"{LOCK}: tag does not resolve to a commit in the local source") from None
    if commit != resolved.decode("ascii").strip():
        raise CheckError(f"{LOCK}: commit does not match the local tag")
    return commit


def pinned_skills(source, commit):
    records = git(source, "ls-tree", "-r", "-t", "-z", "--full-tree", commit, "--", "skills/")
    skills = {}
    entries = {}
    for record in filter(None, records.split(b"\0")):
        metadata, raw_path = record.split(b"\t", 1)
        git_mode, _, oid = metadata.split()
        path = os.fsdecode(raw_path)
        if sensitive(path):
            raise CheckError("pinned skills tree contains a sensitive path (not read)")
        if path == "skills":
            continue
        _, skill, *relative = path.split("/")
        if not relative and git_mode == b"120000":
            raise CheckError("pinned skills tree contains a top-level symlink")
        if skill == "verify-template":
            continue
        if relative:
            entries.setdefault(skill, {})["/".join(relative)] = (git_mode, oid)
    for skill, tree in entries.items():
        skill_file_mode = tree.get("SKILL.md", (None,))[0]
        if skill_file_mode == b"120000":
            raise CheckError("pinned skills tree contains a symlinked SKILL.md")
        if skill_file_mode not in FILE_MODES:
            continue
        if not SKILL_ID.fullmatch(skill):
            raise CheckError("pinned skills tree contains an invalid skill id")
        if any(entry[0] not in FILE_MODES | {b"040000"} for entry in tree.values()):
            raise CheckError(f"skills/{skill}: pinned skill contains a non-regular entry")
        skills[skill] = tree
    if not skills:
        raise CheckError("pinned source contains no installable skills")
    return skills


def match_tree(source, directory, expected, prefix=""):
    if not stat.S_ISDIR(mode(directory)):
        return False
    actual = set()
    for path in directory.iterdir():
        relative = prefix + path.name
        if sensitive(relative):
            raise CheckError("vendored skill contains a sensitive path (not read)")
        actual.add(relative)
        if relative not in expected:
            return False
        git_mode, oid = expected[relative]
        if git_mode == b"040000":
            if not match_tree(source, path, expected, relative + "/"):
                return False
        else:
            local_mode = mode(path)
            if not stat.S_ISREG(local_mode):
                return False
            if bool(local_mode & stat.S_IXUSR) != (git_mode == b"100755"):
                return False
            if path.read_bytes() != git(source, "cat-file", "blob", oid.decode("ascii")):
                return False
    wanted = {name for name in expected if name.rpartition("/")[0] == prefix.rstrip("/")}
    return actual == wanted


def check(source, project):
    skills = pinned_skills(source, read_pin(project, source))
    for folder in (".agents", ".agents/skills", ".claude", ".claude/skills"):
        if not stat.S_ISDIR(mode(project / folder)):
            raise CheckError(f"{folder}: expected a real directory")
    for skill, tree in skills.items():
        vendored = f".agents/skills/{skill}"
        link = f".claude/skills/{skill}"
        if not match_tree(source, project / vendored, tree):
            raise CheckError(f"{vendored}: content or file modes differ from the pinned source")
        path = project / link
        if not stat.S_ISLNK(mode(path)) or os.readlink(path) != f"../../{vendored}":
            raise CheckError(f"{link}: expected relative symlink to ../../{vendored}")
    print(f"check-skills-lock: OK ({len(skills)} pinned skills)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="local Git repository containing the release tag")
    parser.add_argument("--project", type=Path, required=True, help="consumer project with a cstack lock")
    args = parser.parse_args()
    try:
        check(args.source, args.project)
    except (CheckError, OSError) as exc:
        detail = str(exc) if isinstance(exc, CheckError) else "could not inspect installation"
        print(f"check-skills-lock: {detail}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
