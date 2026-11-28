import os
from pathlib import PurePosixPath
import subprocess


class CheckError(Exception):
    """A diagnostic safe to show without dumping file contents."""


def git(repo, *args, env=None):
    result = subprocess.run(
        ["git", "--no-replace-objects", "-C", os.fspath(repo), *args],
        env={**(os.environ if env is None else env), "GIT_NO_LAZY_FETCH": "1"},
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode:
        raise CheckError(f"git {args[0]} failed (exit {result.returncode})")
    return result.stdout


def sensitive(path):
    """Classify known secret paths from their names alone, at any depth."""
    private_names = {
        ".git", ".ssh", ".gnupg", ".aws", ".netrc", ".npmrc", ".pypirc",
        "auth.json", "service.json", "service-account.json",
    }
    private_stems = {
        "credentials", "credential", "token", "tokens", "access_token",
        "api_key", "apikey", "key", "keys", "private_key", "secrets", "secret",
    }
    # Match bare credential names and common credential storage formats, not
    # every file sharing the stem (e.g. key.py, token.test.js, secret.md).
    private_extensions = {
        "bak", "backup", "cfg", "conf", "ini", "json", "local", "old",
        "properties", "toml", "txt", "xml", "yaml", "yml",
    }
    for part in PurePosixPath(path).parts:
        name = part.lower()
        stem, _, suffix = name.lstrip(".").partition(".")
        extension = suffix.partition(".")[0]
        if (
            name in private_names
            or name.startswith((".env", "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519"))
            or (
                stem.replace("-", "_") in private_stems
                and (not suffix or extension in private_extensions)
            )
            or name.endswith((".pem", ".key", ".p12", ".pfx", ".kdbx"))
        ):
            return True
    return False
