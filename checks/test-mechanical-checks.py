"""Focused offline tests for the two mechanical CI checks."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from mechanical_common import CheckError, git, sensitive


ROOT = Path(__file__).resolve().parent.parent
CHECKS = ROOT / "checks"


def require(condition, message):
    if not condition:
        raise CheckError(message)


def run_check(name, *args, expected=0, diagnostic=None, hidden=(), env=None):
    result = subprocess.run(
        [sys.executable, "-B", str(CHECKS / f"{name}.py"), *args],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    require(not any(item in result.stdout for item in hidden), f"{name}: output leaked fixture content")
    require(
        result.returncode == expected,
        f"{name}: got exit {result.returncode}, expected {expected}",
    )
    if diagnostic is not None:
        require(diagnostic.encode() in result.stdout, f"{name}: missing diagnostic: {diagnostic}")
    print(f"{name}: exit {result.returncode} ({diagnostic or 'OK'})")


def test_paths(tmp):
    project = tmp / "path fixture"
    git(tmp, "init", "-q", str(project))
    linux = b"/" + b"home/fixture-user/project"
    mac = b"/" + b"Users/fixture-user/project"
    unicode_home = ("/" + "Users/María Pérez/project").encode()
    (project / "not-tracked.txt").write_bytes(linux)
    (project / "linux.txt").write_bytes(b"ordinary line\n")
    (project / "mac.txt").write_bytes(b"ordinary line\n")
    benign_names = ("key.py", "token.test.js", "secret.md")
    for name in benign_names:
        (project / name).write_bytes(b"ordinary line\n")
    git(project, "add", "--", "linux.txt", "mac.txt", *benign_names)
    args = ("--repo", str(project))
    run_check("check-no-personal-paths", *args)

    for name in benign_names:
        (project / name).write_bytes(linux + b"\n")
        run_check(
            "check-no-personal-paths", *args, expected=1,
            diagnostic=f"'{name}':1: absolute home path", hidden=(linux,),
        )
        (project / name).write_bytes(b"ordinary line\n")

    (project / "linux.txt").write_bytes(b"ordinary line\n" + linux + b"\n")
    run_check(
        "check-no-personal-paths", *args, expected=1,
        diagnostic="'linux.txt':2: absolute home path", hidden=(linux,),
    )
    (project / "linux.txt").write_bytes(b"ordinary line\n")
    (project / "mac.txt").write_bytes(mac + b"\n")
    run_check(
        "check-no-personal-paths", *args, expected=1,
        diagnostic="'mac.txt':1: absolute home path", hidden=(mac,),
    )
    (project / "mac.txt").write_bytes(unicode_home + b"\n")
    run_check(
        "check-no-personal-paths", *args, expected=1,
        diagnostic="'mac.txt':1: absolute home path", hidden=(unicode_home,),
    )
    (project / "mac.txt").write_bytes(b"ordinary line\n")

    for name in (
        "nested/.env.local", "nested/auth.json", "nested/service.json",
        "nested/.ssh/config", "nested/client.pem", "nested/secrets/config",
        "nested/api-key.json.bak",
    ):
        require(sensitive(name), f"expected sensitive path classification for fixture: {name}")

    credential = "token.json"
    (project / credential).write_bytes(linux + b"\n")
    git(project, "add", "--", credential)
    run_check(
        "check-no-personal-paths", *args, expected=1,
        diagnostic="sensitive tracked path (not read)",
        hidden=(credential.encode(), linux, b"absolute home path"),
    )
    run_check("check-no-personal-paths", "--repo", str(ROOT), diagnostic="check-no-personal-paths: OK")


def test_skills(tmp):
    source = tmp / "pinned source"
    project = tmp / "consumer project"
    project.mkdir()
    commit = git(ROOT, "rev-parse", "--verify", "HEAD^{commit}").decode().strip()
    object_format = git(ROOT, "rev-parse", "--show-object-format").decode().strip()
    objects = os.fsdecode(
        git(ROOT, "rev-parse", "--path-format=absolute", "--git-path", "objects").rstrip(b"\n")
    )
    # Use the real HEAD objects read-only. The fixture has its own Git
    # metadata and tag, no remote and no checkout of the producer tree.
    quoted_objects = '"' + objects.replace("\\", "\\\\").replace('"', '\\"') + '"'
    env = {
        **os.environ,
        "GIT_ALTERNATE_OBJECT_DIRECTORIES": quoted_objects,
        "GIT_ALLOW_PROTOCOL": "",
        "GIT_NO_LAZY_FETCH": "1",
    }
    git(tmp, "init", "-q", f"--object-format={object_format}", str(source), env=env)
    tag = "v0.0.0-ci"
    git(source, "tag", "--no-sign", tag, commit, env=env)
    paths = git(source, "ls-tree", "-r", "-t", "--name-only", "-z", commit, "--", "skills/", env=env)
    require(
        not any(sensitive(os.fsdecode(path)) for path in paths.split(b"\0")),
        "skills tree contains a sensitive path (not read)",
    )
    install_dir = source / "install"
    install_dir.mkdir()
    installer = install_dir / "cstack-install"
    installer.write_bytes(git(source, "show", f"{commit}:install/cstack-install", env=env))

    agents = project / ".agents/skills"
    claude = project / ".claude/skills"
    claude.mkdir(parents=True)
    unrelated = agents / "verify-ci-consumer"
    unrelated.mkdir(parents=True)
    (unrelated / "SKILL.md").write_text("Consumer-owned skill\n", encoding="utf-8")
    (claude / unrelated.name).symlink_to(f"../../.agents/skills/{unrelated.name}")

    result = subprocess.run(
        ["sh", str(installer), "--version", tag, "--project", str(project)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    require(result.returncode == 0, f"isolated cstack-install: got exit {result.returncode}, expected 0")
    print("isolated cstack-install at producer HEAD: exit 0")
    require(not (agents / "verify-template").exists(), "installer copied verify-template")
    require(not (claude / "verify-template").is_symlink(), "installer linked verify-template")
    require(
        (unrelated / "SKILL.md").read_text(encoding="utf-8") == "Consumer-owned skill\n"
        and os.readlink(claude / unrelated.name) == f"../../.agents/skills/{unrelated.name}",
        "installer modified an unrelated skill",
    )
    vendored = sorted(path.name for path in agents.iterdir() if path != unrelated)
    require(bool(vendored), "installer did not install any cstack skill")
    skill = vendored[0]
    args = ("--source", str(source), "--project", str(project))
    name = "check-skills-lock"
    run_check(name, *args, env=env)

    content = agents / skill / "SKILL.md"
    original = content.read_bytes()
    content.write_bytes(original + b"\nFixture drift\n")
    run_check(name, *args, expected=1, diagnostic=f".agents/skills/{skill}: content or file modes differ", env=env)
    content.write_bytes(original)

    link = claude / skill
    original_target = os.readlink(link)
    link.unlink()
    link.symlink_to(f"../../.agents/skills/{unrelated.name}")
    run_check(name, *args, expected=1, diagnostic=f".claude/skills/{skill}: expected relative symlink", env=env)
    link.unlink()
    link.symlink_to(original_target)

    lock = project / ".opencode/cstack.lock.json"
    original_lock = lock.read_bytes()
    lock.write_text(json.dumps({**json.loads(original_lock), "commit": "0" * len(commit)}), encoding="utf-8")
    run_check(name, *args, expected=1, diagnostic="cstack.lock.json: commit does not match the local tag", env=env)
    lock.unlink()
    run_check(name, *args, expected=1, diagnostic="cstack.lock.json: expected a regular lock file", env=env)
    lock.write_bytes(original_lock)
    run_check(name, *args, env=env)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("check", choices=("paths", "skills"))
    args = parser.parse_args()
    try:
        with TemporaryDirectory(prefix="cstack-mechanical-") as tmp:
            {"paths": test_paths, "skills": test_skills}[args.check](Path(tmp))
    except (CheckError, OSError) as exc:
        detail = str(exc) if isinstance(exc, CheckError) else "could not prepare or inspect a fixture"
        print(detail, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
