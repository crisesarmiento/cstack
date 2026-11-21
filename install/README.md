# Installing cstack into a project

`cstack-install` vendors a **pinned** cstack release into a consumer project.
It implements option A of the structure spec
([docs/specs/0001-structure-and-versioning.md](../docs/specs/0001-structure-and-versioning.md) §6):
the consumer commits real copies of the skills plus a lock file, so the pin
travels with the checkout (Orca worktrees, clones, CI) with no runtime
dependency on this repository.

```text
cstack-install --version v0.1.0 --project /path/to/repo
```

Run it **from a checkout of cstack** (the script uses the repository it lives
in as its source). On success the consumer project contains:

```
.agents/skills/
  correct/SKILL.md            # canonical copy of that release (do not edit)
  sharpen/SKILL.md
.claude/skills/
  correct -> ../../.agents/skills/correct    # relative symlink
  sharpen -> ../../.agents/skills/sharpen
.opencode/
  cstack.lock.json            # { "version", "tag", "commit" }
```

The commit recorded in the lock is the exact commit the tag resolves to.

## Requirements

* POSIX `sh` and `git`. Nothing else: no sudo, no package installs, no
  other languages, no `tar` (the tree is extracted with git itself).
* Standard core utilities: `cp`, `ln`, `mkdir`, `rm`, `mv`, `diff`,
  `readlink`, `mktemp`, `dirname`, `basename`, `chmod`, `cat`, `printf`.

## How the version is resolved

1. `--version vX.Y.Z` selects a **tag**. Formats: `vMAJOR.MINOR.PATCH`,
   optionally with a semver pre-release/build suffix (`v0.1.0-rc.1`).
   Anything else is rejected before any git work happens.
2. If the tag already exists in the local checkout, it is used as is and
   **no network access happens at all**.
3. If it does not, the script fetches **exactly that one tag** from the
   `origin` remote (`git fetch --no-tags origin refs/tags/X:refs/tags/X`).
   That fetch is the only network operation the script can ever perform.
   There is no clone, no branch tracking, no `sudo`.
4. The skills come from the tag's **git tree**, never from the working
   copy. A dirty checkout, or a `HEAD` that has moved past the tag, cannot
   leak into a consumer; the lock records the commit the tag points at.

If the tag's `skills/` has no installable skill (for example a pre-release
commit without skills), the install stops and nothing is written.

## What it writes, and what it never touches

| Writes (only these) | Never touches |
| --- | --- |
| `.agents/skills/<id>/` copies of every skill of the tag **except `verify-template`** | `verify-template` (spec 0002: it generates project-local skills; it is not vendored) |
| `.claude/skills/<id>` relative symlinks → `../../.agents/skills/<id>` | consumer-generated `verify-<app>` skills, in either folder |
| `.opencode/cstack.lock.json` (atomically: written to a temp file, then renamed) | the live preset `.opencode/oh-my-opencode-slim.json` |
| directories `.agents/skills/`, `.claude/skills/`, `.opencode/` when missing | unrelated skills and any other existing file |

Loose files under the tag's `skills/` that are not skill folders are
reported and ignored, not vendored. A skill folder whose name is not a
valid id (lowercase letters, digits, hyphens, ≤ 64 chars) makes the whole
install refuse: the tag is treated as broken, not trusted.

## Idempotence, conflicts and `--force`

* Re-running the same version is a **no-op**: paths that already match are
  left byte-for-byte alone, and the run reports "nothing to do".
* An existing cstack target that **differs** from the tag — a modified
  vendored copy, a symlink where a directory belongs, a real file where the
  `.claude` link belongs — makes the run **refuse with exit 1**, listing
  every conflicting path. Refusals happen in a preflight pass: a refused
  run leaves the project exactly as it was, even when several skills were
  already installable.
* `--force` lets the run replace those differing cstack-owned targets. It
  replaces the link or directory **itself** (`rm` never follows a
  symlink), so content outside the consumer is never damaged, and it only
  ever touches the ids that belong to the pack — never unrelated skills,
  never `verify-*`, never the preset.
* The lock is cstack's own record: it is updated on every successful run.
  If the tag's skills are byte-identical to what is installed (only the
  release number moved), the lock updates **without** `--force`.

### Upgrading

An upgrade is the same command with a new tag:

```text
cstack-install --version v0.2.0 --project /path/to/repo
```

If skill content changed between the two releases, add `--force` (vendored
copies are not supposed to be edited, so a differing copy is treated as a
conflict on purpose). Commit the result and open the PR in the consumer —
the script never commits anything.

### Uninstalling

Remove the cstack-owned paths (keep everything else, including your
generated `verify-*` skills):

```text
rm -rf .agents/skills/<id> .claude/skills/<id> .opencode/cstack.lock.json
```

## Symlink and path safety

* Intermediate layout components (`.agents`, `.agents/skills`, `.claude`,
  `.claude/skills`, `.opencode`) must be real directories or absent. If one
  exists as a symlink or a regular file, the install is a **hard error**
  — `--force` does not override it, because that would write through a
  link to an unknown location.
* Every path is quoted; directories and checkouts with spaces in their
  names work, including a spaced `TMPDIR`.
* `--project` must be an existing directory (validated before any git or
  network work). It does not need to be a git repository.

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | success, including a run with nothing to do |
| 1 | refused (conflict) or failed: missing tag, broken tag, missing skills tree, git/IO error |
| 2 | usage error: bad arguments, invalid `--version` format, invalid/missing `--project` |

## Testing

```text
sh install/test-cstack-install.sh
```

The suite is self-contained and dependency-free: it builds throwaway
fixture git repos (source with tags, bare origin, consumer) in a temp
directory and covers copies, `verify-template` exclusion, link targets,
the pinned commit against a dirty/ahead checkout, idempotence, refusal
and `--force`, preservation of unrelated skills and the live preset, paths
with spaces, invalid arguments/tags/projects, symlink and layout
collisions, single-tag fetching, lightweight and pre-release tags, and
hostile tag contents. It needs no network: the fixture `origin` is a local
bare repository. The same suite runs in CI via
[`.github/workflows/installer.yml`](../.github/workflows/installer.yml).

For a public, tool-managed alternative (`npx skills add
crisesarmiento/cstack@vX.Y.Z`), see spec 0001 §6; the committed layout above
is the default for cstack's own projects.
