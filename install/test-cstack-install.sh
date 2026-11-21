#!/bin/sh
# Test suite for install/cstack-install (option A of docs/specs/0001 section 6).
#
# Self-contained and dependency-free: POSIX sh plus git and the usual core
# utilities. Every fixture (source repos, tags, origins, consumer repos) is
# created inside a throwaway temp directory; the real repository is never
# tagged, fetched from, or written to. The "origin" remotes are local bare
# repositories, so no network access is ever needed.
#
# Usage: sh install/test-cstack-install.sh   (run from anywhere)
#
# Coverage:
#   S1  fresh install: copies, exclusion, links, lock, preservation
#   S2  lock pins the tag's commit, not a dirty/ahead checkout
#   S3  idempotence (byte-for-byte no-op on re-run)
#   S4  differing targets refused, atomically (no partial install)
#   S5  --force replaces differing targets
#   S6  lock-only upgrade (identical skills) needs no --force
#   S7  upgrade with changed skills: refused, then --force; verify-* preserved
#   S8  paths with spaces (project, source checkout, TMPDIR)
#   S9  usage errors: invalid args/tag format/project (exit 2, no mutations)
#   S10 well-formed but nonexistent tag (exit 1, consumer untouched)
#   S11 local tag installs with no remote at all (no network path)
#   S12 fetching a missing tag pulls in exactly that one tag
#   S13 lightweight tags resolve to their commit
#   S14 pre-release tag format (v0.1.0-rc.1)
#   S15 tag without a skills/ tree is refused
#   S16 project without git works
#   S17 relative --project path from a different cwd
#   S18 symlink collisions: refused; --force replaces without damage outside
#   S19 lock path collisions (directory / symlink pointing elsewhere)
#   S20 layout components that are not real directories (hard error)
#   S21 hostile/junk entries in a tag: bad ids refused, junk ignored
#   S22 tag and same-named branch: the pin resolves the tag only
#   S23 symlink inside an existing skill copy: conflict before diff, never
#       followed by it
#   S24 symlink inside a skill of the tag: the tag is refused

# ------------------------------------------------------------------ setup ---

HERE=$(cd -P -- "$(dirname -- "$0")" 2>/dev/null && pwd -P)
[ -n "$HERE" ] || { echo "cannot locate the test script directory"; exit 1; }
INSTALLER="$HERE/cstack-install"

PASS=0
FAIL=0
TMP=$(mktemp -d) || { echo "cannot create a temp directory"; exit 1; }
chmod 755 "$TMP"
OUT="$TMP/last-out"
ERR="$TMP/last-err"
IRC=99      # exit code of the last installer run
CUR=""      # installer copy under test (staged inside the current fixture)
trap 'rm -rf -- "$TMP"' EXIT

ok() { PASS=$((PASS + 1)); }
bad() {
    FAIL=$((FAIL + 1))
    printf '  FAIL: %s\n' "$*"
}

step() { printf '\n== %s\n' "$*"; }

assert_rc()  { if [ "$2" = "$3" ]; then ok; else bad "$1: exit $3, expected $2"; fi; }
assert_eq()  { if [ "$2" = "$3" ]; then ok; else bad "$1: expected [$2], actual [$3]"; fi; }
assert_true()  { lb=$1; shift; if "$@"; then ok; else bad "$lb"; fi; }
assert_false() { lb=$1; shift; if "$@"; then bad "$lb"; else ok; fi; }

# exact-file-content assertion (fixtures are small text files)
file_is() {
    fi_desc=$1 fi_path=$2 fi_want=$3
    fi_got=$(cat -- "$fi_path" 2>/dev/null)
    if [ "$fi_got" = "$fi_want" ]; then ok; else bad "$fi_desc: content is [$fi_got], expected [$fi_want]"; fi
}

assert_file_has() {   # label, file, literal substring
    if grep -qF -- "$3" "$2" 2>/dev/null; then ok; else bad "$1: $2 does not contain [$3]"; fi
}

out_has() { grep -qF -- "$1" "$OUT" 2>/dev/null; }
err_has() { grep -qF -- "$1" "$ERR" 2>/dev/null; }

# run the installer copy under test; captures rc, stdout, stderr
run() {
    rm -f -- "$OUT" "$ERR"
    "$CUR" "$@" >"$OUT" 2>"$ERR"
    IRC=$?
}

# Canonical textual snapshot of a directory tree (skips .git): symlinks with
# their targets, directories, files with a POSIX cksum. Two equal snapshots
# mean "byte-for-byte unchanged".
snapshot() {
    ( cd -- "$1" || exit 1
      find . -name .git -prune -o -print | LC_ALL=C sort | while read -r sp_path; do
          if [ -L "$sp_path" ]; then
              printf 'L %s -> %s\n' "$sp_path" "$(readlink "$sp_path")"
          elif [ -d "$sp_path" ]; then
              printf 'D %s\n' "$sp_path"
          elif [ -f "$sp_path" ]; then
              printf 'F %s %s\n' "$sp_path" "$(cksum < "$sp_path")"
          else
              printf '? %s\n' "$sp_path"
          fi
      done )
}

# ------------------------------------------------- fixture: source repos ----

# One "kitchen sink" history with all the tag shapes the suite needs:
#   v0.0.1       annotated, commit without skills/ (refused by the installer)
#   v0.1.0       annotated, skills: correct (+refs,+exec script), sharpen,
#                verify-template
#   v0.1.1       annotated, identical skills, only VERSION changed
#   v0.1.0-rc.1  annotated pre-release tag on the v0.1.1 commit
#   v0.2.0       annotated, correct content changed, review-gate added
#   v0.3.0       lightweight tag on the v0.2.0 commit
KW="$TMP/ks-work"
ORIGIN="$TMP/ks-origin.git"

git -c init.defaultBranch=main init -q "$KW" 2>/dev/null
ks() { git -C "$KW" "$@"; }
ks_commit() {
    ks add -A >/dev/null 2>&1
    ks -c user.name=T -c user.email=t@example.com commit -qm "$1" >/dev/null 2>&1
}

# c0: no skills yet
printf '0.0.0\n' > "$KW/VERSION"
ks_commit 'c0'
ks tag -a v0.0.1 -m t0 >/dev/null 2>&1

# c1: the v0.1.0 skills
mkdir -p "$KW/skills/correct/references" "$KW/skills/correct/scripts" \
         "$KW/skills/sharpen" "$KW/skills/verify-template"
printf 'correct v0.1.0\n' > "$KW/skills/correct/SKILL.md"
printf 'notes v0.1.0\n' > "$KW/skills/correct/references/notes.md"
printf '#!/bin/sh\necho ok\n' > "$KW/skills/correct/scripts/run.sh"
chmod 755 "$KW/skills/correct/scripts/run.sh"
printf 'sharpen body\n' > "$KW/skills/sharpen/SKILL.md"
printf 'template body\n' > "$KW/skills/verify-template/SKILL.md"
printf '0.1.0\n' > "$KW/VERSION"
ks_commit 'c1'
ks tag -a v0.1.0 -m t1 >/dev/null 2>&1

# c2: identical skills, only VERSION changes (lock-only upgrade case)
printf '0.1.1\n' > "$KW/VERSION"
ks_commit 'c2'
KS_C2=$(ks rev-parse HEAD)
ks tag -a v0.1.1 -m t2 >/dev/null 2>&1
ks tag -a v0.1.0-rc.1 "$KS_C2" -m rc >/dev/null 2>&1

# c3: correct changes and a new skill appear (content upgrade case)
printf 'correct v0.2.0\n' > "$KW/skills/correct/SKILL.md"
mkdir -p "$KW/skills/review-gate"
printf 'review-gate body\n' > "$KW/skills/review-gate/SKILL.md"
printf '0.2.0\n' > "$KW/VERSION"
ks_commit 'c3'
ks tag -a v0.2.0 -m t3 >/dev/null 2>&1
ks tag v0.3.0 >/dev/null 2>&1

git clone -q --bare "$KW" "$ORIGIN" 2>/dev/null
assert_eq "fixture sanity: origin carries six tags" \
    "6" "$(git -C "$ORIGIN" tag -l | wc -l | tr -d ' ')"

# stage a copy of the installer inside an already-built fixture repo (the
# installer resolves its source checkout from its own location)
stage_only() {
    mkdir -p "$1/install"
    cp -- "$INSTALLER" "$1/install/cstack-install"
    chmod 755 "$1/install/cstack-install"
    CUR="$1/install/cstack-install"
}

# clone of the fixture origin, with the installer staged inside it (the copy
# is untracked, which also proves content is read from the tag, not the
# working tree)
clone_src() {
    git clone -q "$ORIGIN" "$1" >/dev/null 2>&1
    stage_only "$1"
}

# consumer project fixture
#   rich : git repo + unrelated skill + generated verify-londinium + live
#          preset + its .claude link (things the installer must preserve)
#   bare : git repo with just a README
#   nogit: plain directory, not a git repo
build_consumer() {
    bc_dir=$1 bc_mode=$2
    mkdir -p "$bc_dir"
    if [ "$bc_mode" != nogit ]; then
        git -c init.defaultBranch=main init -q "$bc_dir" 2>/dev/null
    fi
    printf 'consumer readme\n' > "$bc_dir/README.md"
    if [ "$bc_mode" = rich ]; then
        mkdir -p "$bc_dir/.agents/skills/my-own-skill" \
                 "$bc_dir/.agents/skills/verify-londinium" \
                 "$bc_dir/.claude/skills" "$bc_dir/.opencode"
        printf 'my own skill\n' > "$bc_dir/.agents/skills/my-own-skill/SKILL.md"
        printf 'verify londinium generated\n' > "$bc_dir/.agents/skills/verify-londinium/SKILL.md"
        printf 'live preset, hands off\n' > "$bc_dir/.opencode/oh-my-opencode-slim.json"
        ln -s ../../.agents/skills/verify-londinium "$bc_dir/.claude/skills/verify-londinium"
    fi
    if [ "$bc_mode" != nogit ]; then
        git -C "$bc_dir" add -A >/dev/null 2>&1
        git -C "$bc_dir" -c user.name=T -c user.email=t@example.com \
            commit -qm init >/dev/null 2>&1
    fi
}

# ------------------------------------------------------------- S0 basics ----

step "S0 installer ships executable and syntactically valid"
assert_true "installer exists" test -f "$INSTALLER"
assert_true "installer is executable" test -x "$INSTALLER"
assert_true "installer passes sh -n" sh -n "$INSTALLER"
assert_true "test suite passes sh -n" sh -n "$0"

# ---------------------------------------------------- S1 fresh install ------

step "S1 fresh install: copies, exclusion, links, lock, preservation"
SRC="$TMP/s1-src"; clone_src "$SRC"
CONS="$TMP/s1-cons"; build_consumer "$CONS" rich
run --version v0.1.0 --project "$CONS"
assert_rc "install succeeds" 0 "$IRC"
# copies from the tag
assert_true "correct SKILL.md copied" test -f "$CONS/.agents/skills/correct/SKILL.md"
file_is "correct has tag content" "$CONS/.agents/skills/correct/SKILL.md" 'correct v0.1.0'
file_is "nested reference copied" "$CONS/.agents/skills/correct/references/notes.md" 'notes v0.1.0'
assert_true "nested script copied" test -f "$CONS/.agents/skills/correct/scripts/run.sh"
assert_true "exec bit preserved on scripts" test -x "$CONS/.agents/skills/correct/scripts/run.sh"
file_is "sharpen copied with tag content" "$CONS/.agents/skills/sharpen/SKILL.md" 'sharpen body'
# exclusion
assert_false "verify-template not vendored into .agents" test -e "$CONS/.agents/skills/verify-template"
assert_false "verify-template not linked into .claude" test -e "$CONS/.claude/skills/verify-template"
assert_true "exclusion reported in output" out_has "verify-template"
# relative links
assert_true "claude link for correct exists" test -L "$CONS/.claude/skills/correct"
assert_eq "correct link is the relative target" \
    "../../.agents/skills/correct" "$(readlink "$CONS/.claude/skills/correct")"
assert_true "link resolves to the vendored file" test -f "$CONS/.claude/skills/correct/SKILL.md"
assert_eq "sharpen link is the relative target" \
    "../../.agents/skills/sharpen" "$(readlink "$CONS/.claude/skills/sharpen")"
# lock with the actual pinned commit, exact keys and shape
LOCK="$CONS/.opencode/cstack.lock.json"
assert_true "lock file exists" test -f "$LOCK"
C100=$(git -C "$SRC" rev-parse 'refs/tags/v0.1.0^{commit}')
assert_file_has "lock version" "$LOCK" '"version": "0.1.0"'
assert_file_has "lock tag" "$LOCK" '"tag": "v0.1.0"'
assert_file_has "lock pins the tag's commit" "$LOCK" "\"commit\": \"$C100\""
EXP_LOCK_S1='{
  "version": "0.1.0",
  "tag": "v0.1.0",
  "commit": "'"$C100"'"
}'
assert_eq "lock is exactly {version, tag, commit} (keys, order, shape)" \
    "$EXP_LOCK_S1" "$(cat -- "$LOCK")"
assert_eq "lock ends with a newline" "" "$(tail -c 1 "$LOCK")"
assert_eq "no lock temp files left behind" "" \
    "$(find "$CONS/.opencode" -name '.cstack.lock.*' -print)"
# preservation of everything the installer must never touch
file_is "unrelated skill untouched" "$CONS/.agents/skills/my-own-skill/SKILL.md" 'my own skill'
file_is "generated verify-* untouched" "$CONS/.agents/skills/verify-londinium/SKILL.md" 'verify londinium generated'
assert_eq "verify-* claude link untouched" \
    "../../.agents/skills/verify-londinium" "$(readlink "$CONS/.claude/skills/verify-londinium")"
file_is "live preset untouched" "$CONS/.opencode/oh-my-opencode-slim.json" 'live preset, hands off'
file_is "consumer readme untouched" "$CONS/README.md" 'consumer readme'
assert_true "lock content is valid JSON shape" out_has "lock: .opencode/cstack.lock.json written"

# ------------------------------------------- S2 dirty/ahead source repo -----

step "S2 lock pins the tag's commit, not a dirty or ahead checkout"
SRC2="$TMP/s2-src"; clone_src "$SRC2"
# move HEAD one commit past the tag ...
printf 'sharpen AHEAD\n' > "$SRC2/skills/sharpen/SKILL.md"
printf '0.1.0-dirty\n' > "$SRC2/VERSION"
git -C "$SRC2" add -A >/dev/null 2>&1
git -C "$SRC2" -c user.name=T -c user.email=t@example.com commit -qm ahead >/dev/null 2>&1
# ... and additionally leave an uncommitted change in the working tree
printf 'DIRTY CORRECT\n' > "$SRC2/skills/correct/SKILL.md"
S2_TAGC=$(git -C "$SRC2" rev-parse 'refs/tags/v0.1.0^{commit}')
S2_HEAD=$(git -C "$SRC2" rev-parse HEAD)
assert_true "fixture sanity: HEAD is past the tag" test "$S2_TAGC" != "$S2_HEAD"
assert_true "fixture sanity: working tree is dirty" \
    test -n "$(git -C "$SRC2" status --porcelain)"
CONS2="$TMP/s2-cons"; build_consumer "$CONS2" bare
run --version v0.1.0 --project "$CONS2"
assert_rc "install from a dirty checkout succeeds" 0 "$IRC"
file_is "installed correct is tag content, not the dirty tree" \
    "$CONS2/.agents/skills/correct/SKILL.md" 'correct v0.1.0'
file_is "installed sharpen is tag content, not HEAD" \
    "$CONS2/.agents/skills/sharpen/SKILL.md" 'sharpen body'
assert_file_has "lock pins the tag commit" \
    "$CONS2/.opencode/cstack.lock.json" "\"commit\": \"$S2_TAGC\""
assert_false "lock does not pin the ahead HEAD" \
    grep -qF "\"commit\": \"$S2_HEAD\"" "$CONS2/.opencode/cstack.lock.json"

# --------------------------------------------------------- S3 idempotence ---

step "S3 idempotence: a second run changes nothing"
SNAP1=$(snapshot "$CONS")
run --version v0.1.0 --project "$CONS"
assert_rc "second run succeeds" 0 "$IRC"
SNAP2=$(snapshot "$CONS")
assert_eq "second run is a byte-for-byte no-op" "$SNAP1" "$SNAP2"
assert_true "second run reports the no-op" out_has "already matches"

# ------------------------------------- S4 differing targets: refusal -------

step "S4 differing existing targets are refused, atomically"
SRC4="$TMP/s4-src"; clone_src "$SRC4"
CONS4="$TMP/s4-cons"; build_consumer "$CONS4" bare
mkdir -p "$CONS4/.agents/skills/correct" "$CONS4/.claude/skills"
printf 'user modified correct\n' > "$CONS4/.agents/skills/correct/SKILL.md"
printf 'user file where the link belongs\n' > "$CONS4/.claude/skills/sharpen"
run --version v0.1.0 --project "$CONS4"
assert_rc "differing targets are refused" 1 "$IRC"
assert_true "refusal names the skill copy" err_has ".agents/skills/correct"
assert_true "refusal names the link path" err_has ".claude/skills/sharpen"
assert_true "refusal suggests --force" err_has "--force"
assert_true "refusal says nothing was modified" err_has "Nothing was modified"
# atomicity: not one path was created or changed
assert_false "no .opencode created" test -e "$CONS4/.opencode"
assert_false "no sharpen copy created" test -e "$CONS4/.agents/skills/sharpen"
file_is "user's correct content intact" "$CONS4/.agents/skills/correct/SKILL.md" 'user modified correct'
file_is "user's file at the link path intact" "$CONS4/.claude/skills/sharpen" 'user file where the link belongs'

# --------------------------------------------- S5 --force replaces them -----

step "S5 --force replaces the differing targets"
run --version v0.1.0 --project "$CONS4" --force
assert_rc "force install succeeds" 0 "$IRC"
file_is "correct replaced with tag content" "$CONS4/.agents/skills/correct/SKILL.md" 'correct v0.1.0'
assert_true "sharpen is now a symlink" test -L "$CONS4/.claude/skills/sharpen"
assert_eq "sharpen link target correct" \
    "../../.agents/skills/sharpen" "$(readlink "$CONS4/.claude/skills/sharpen")"
assert_true "lock written after force" test -f "$CONS4/.opencode/cstack.lock.json"

# ------------------------------------- S6 lock-only upgrade (no --force) ----

step "S6 upgrade to a tag with identical skills needs no --force"
SRC6="$TMP/s6-src"; clone_src "$SRC6"
CONS6="$TMP/s6-cons"; build_consumer "$CONS6" rich
run --version v0.1.0 --project "$CONS6"
assert_rc "first version installs" 0 "$IRC"
run --version v0.1.1 --project "$CONS6"
assert_rc "identical-content upgrade succeeds without --force" 0 "$IRC"
assert_file_has "lock bumped to 0.1.1" "$CONS6/.opencode/cstack.lock.json" '"version": "0.1.1"'
assert_file_has "lock tag bumped to v0.1.1" "$CONS6/.opencode/cstack.lock.json" '"tag": "v0.1.1"'
file_is "skill content unchanged by the lock-only upgrade" \
    "$CONS6/.agents/skills/correct/SKILL.md" 'correct v0.1.0'

# ------------------------------------------- S7 upgrade with new content ----

step "S7 upgrade with changed skills: refused, then --force"
SRC7="$TMP/s7-src"; clone_src "$SRC7"
CONS7="$TMP/s7-cons"; build_consumer "$CONS7" rich
run --version v0.1.0 --project "$CONS7"
assert_rc "first version installs" 0 "$IRC"
run --version v0.2.0 --project "$CONS7"
assert_rc "upgrade with differing skills is refused" 1 "$IRC"
assert_false "no partial new skill installed" test -e "$CONS7/.agents/skills/review-gate"
file_is "old correct untouched by the refusal" "$CONS7/.agents/skills/correct/SKILL.md" 'correct v0.1.0'
assert_file_has "lock still at 0.1.0 after the refusal" \
    "$CONS7/.opencode/cstack.lock.json" '"version": "0.1.0"'
run --version v0.2.0 --project "$CONS7" --force
assert_rc "force upgrade succeeds" 0 "$IRC"
file_is "correct upgraded to v0.2.0" "$CONS7/.agents/skills/correct/SKILL.md" 'correct v0.2.0'
assert_true "new skill installed" test -f "$CONS7/.agents/skills/review-gate/SKILL.md"
assert_eq "new skill linked" \
    "../../.agents/skills/review-gate" "$(readlink "$CONS7/.claude/skills/review-gate")"
assert_file_has "lock bumped to 0.2.0" "$CONS7/.opencode/cstack.lock.json" '"version": "0.2.0"'
file_is "sharpen content unchanged across the upgrade" \
    "$CONS7/.agents/skills/sharpen/SKILL.md" 'sharpen body'
# --force never touches unrelated skills, generated verify-*, or the preset
file_is "unrelated skill survives --force" "$CONS7/.agents/skills/my-own-skill/SKILL.md" 'my own skill'
file_is "generated verify-* survives --force" \
    "$CONS7/.agents/skills/verify-londinium/SKILL.md" 'verify londinium generated'
assert_eq "verify-* claude link survives --force" \
    "../../.agents/skills/verify-londinium" "$(readlink "$CONS7/.claude/skills/verify-londinium")"
file_is "live preset survives --force" "$CONS7/.opencode/oh-my-opencode-slim.json" 'live preset, hands off'

# ------------------------------------------------------- S8 spaces ----------

step "S8 spaces in project path, source path and TMPDIR"
SRC8="$TMP/s8 src checkout"; clone_src "$SRC8"
CONS8="$TMP/s8 pra ject dir"; build_consumer "$CONS8" bare
SPACETMP="$TMP/s8 tmp space"; mkdir -p "$SPACETMP"
( TMPDIR="$SPACETMP" "$CUR" --version v0.1.0 --project "$CONS8" ) >"$OUT" 2>"$ERR"
IRC=$?
assert_rc "install works with spaces everywhere" 0 "$IRC"
assert_true "skills copied under the spaced project" test -f "$CONS8/.agents/skills/correct/SKILL.md"
assert_eq "link correct under the spaced project" \
    "../../.agents/skills/correct" "$(readlink "$CONS8/.claude/skills/correct")"
assert_file_has "lock written under the spaced project" \
    "$CONS8/.opencode/cstack.lock.json" '"tag": "v0.1.0"'
assert_eq "staging in the spaced TMPDIR was cleaned up" "" "$(ls -A "$SPACETMP")"

# -------------------------------------------------- S9 invalid arguments ----

step "S9 usage errors: bad args, tag format, project (exit 2, no mutations)"
# usage errors are validated before any git work, so the real checkout's
# installer can be invoked directly here
CUR="$INSTALLER"
EMPTY9="$TMP/s9-empty"; mkdir -p "$EMPTY9"
badcase() {
    bl_label=$1
    shift
    run "$@"
    assert_rc "$bl_label" 2 "$IRC"
    assert_eq "$bl_label (consumer untouched)" "" "$(ls -A "$EMPTY9")"
}
badcase "no arguments"
badcase "missing --version value" --version
badcase "missing --project value" --version v0.1.0 --project
badcase "--version given without --project" --version v0.1.0
badcase "--project given without --version" --project "$EMPTY9"
badcase "unknown flag" --wat --version v0.1.0 --project "$EMPTY9"
badcase "version without v prefix" --version 0.1.0 --project "$EMPTY9"
badcase "version with two parts" --version v1.2 --project "$EMPTY9"
badcase "version with letters" --version vX.Y.Z --project "$EMPTY9"
badcase "version with four parts" --version v1.2.3.4 --project "$EMPTY9"
badcase "version with a bare trailing hyphen" --version v1.2.3- --project "$EMPTY9"
badcase "version with shell metacharacters" --version 'v1.2.3; rm -rf nope' --project "$EMPTY9"
badcase "empty --version value" --version '' --project "$EMPTY9"
badcase "empty --project value" --version v0.1.0 --project ''
badcase "nonexistent project" --version v0.1.0 --project "$TMP/s9-does-not-exist"
AFILE9="$TMP/s9-a-regular-file"; printf 'x\n' > "$AFILE9"
badcase "project is a regular file" --version v0.1.0 --project "$AFILE9"
run --help
assert_rc "--help exits 0" 0 "$IRC"
assert_true "help documents --version" out_has -- '--version'
assert_true "help documents --project" out_has -- '--project'
assert_true "help documents --force" out_has -- '--force'

# --------------------------------------------- S10 nonexistent tag ----------

step "S10 well-formed but nonexistent tag"
SRC10="$TMP/s10-src"; clone_src "$SRC10"
CONS10="$TMP/s10-cons"; build_consumer "$CONS10" bare
run --version v9.9.9 --project "$CONS10"
assert_rc "missing tag fails" 1 "$IRC"
assert_true "error names the missing tag" err_has "v9.9.9"
assert_false "consumer .agents untouched" test -e "$CONS10/.agents"
assert_false "consumer .claude untouched" test -e "$CONS10/.claude"
assert_false "consumer .opencode untouched" test -e "$CONS10/.opencode"

# --------------------------------- S11 local tag, no remote, no network -----

step "S11 a local tag installs with no remote configured at all"
SRC11="$TMP/s11-src"; clone_src "$SRC11"
git -C "$SRC11" remote remove origin
CONS11="$TMP/s11-cons"; build_consumer "$CONS11" bare
run --version v0.1.0 --project "$CONS11"
assert_rc "local tag needs no origin" 0 "$IRC"
assert_true "output says the tag was found locally" out_has "found locally"
assert_true "lock written" test -f "$CONS11/.opencode/cstack.lock.json"
# but a missing local tag without any remote fails with a clear message
git -C "$SRC11" tag -l | while read -r s11_tag; do
    git -C "$SRC11" tag -d "$s11_tag" >/dev/null 2>&1
done
run --version v0.2.0 --project "$CONS11"
assert_rc "missing tag with no origin fails" 1 "$IRC"
assert_true "error explains there is no origin" err_has "origin"

# -------------------------------- S12 fetch pulls exactly the one tag -------

step "S12 a missing tag is fetched alone (no other tag comes along)"
SRC12="$TMP/s12-src"; clone_src "$SRC12"
git -C "$SRC12" tag -l | while read -r s12_tag; do
    git -C "$SRC12" tag -d "$s12_tag" >/dev/null 2>&1
done
assert_eq "fixture sanity: local tags deleted" "" "$(git -C "$SRC12" tag -l)"
CONS12="$TMP/s12-cons"; build_consumer "$CONS12" bare
run --version v0.1.1 --project "$CONS12"
assert_rc "install via the single-tag fetch" 0 "$IRC"
assert_eq "only the requested tag was fetched" "v0.1.1" "$(git -C "$SRC12" tag -l)"
assert_true "output notes the fetch" out_has "fetched from origin"

# ------------------------------------------------ S13 lightweight tag -------

step "S13 lightweight tags resolve to their commit"
SRC13="$TMP/s13-src"; clone_src "$SRC13"
CONS13="$TMP/s13-cons"; build_consumer "$CONS13" bare
run --version v0.3.0 --project "$CONS13"
assert_rc "lightweight tag installs" 0 "$IRC"
assert_file_has "lock version from the lightweight tag" \
    "$CONS13/.opencode/cstack.lock.json" '"version": "0.3.0"'
assert_file_has "lightweight tag peeled to its commit" \
    "$CONS13/.opencode/cstack.lock.json" \
    "\"commit\": \"$(git -C "$SRC13" rev-parse 'refs/tags/v0.3.0^{commit}')\""

# ------------------------------------------------ S14 pre-release tag --------

step "S14 pre-release tag format"
SRC14="$TMP/s14-src"; clone_src "$SRC14"
CONS14="$TMP/s14-cons"; build_consumer "$CONS14" bare
run --version v0.1.0-rc.1 --project "$CONS14"
assert_rc "pre-release tag installs" 0 "$IRC"
assert_file_has "lock version keeps the pre-release" \
    "$CONS14/.opencode/cstack.lock.json" '"version": "0.1.0-rc.1"'
assert_file_has "lock tag keeps the pre-release" \
    "$CONS14/.opencode/cstack.lock.json" '"tag": "v0.1.0-rc.1"'
assert_file_has "lock pins the pre-release tag's commit" \
    "$CONS14/.opencode/cstack.lock.json" \
    "\"commit\": \"$(git -C "$SRC14" rev-parse 'refs/tags/v0.1.0-rc.1^{commit}')\""

# ------------------------------------------ S15 tag without skills/ ---------

step "S15 a tag without a skills/ tree is refused"
SRC15="$TMP/s15-src"; clone_src "$SRC15"
CONS15="$TMP/s15-cons"; build_consumer "$CONS15" bare
run --version v0.0.1 --project "$CONS15"
assert_rc "no-skills tag fails" 1 "$IRC"
assert_true "error mentions skills/" err_has "skills/"
assert_false "consumer untouched" test -e "$CONS15/.agents"

# ------------------------------------------------ S16 non-git project -------

step "S16 a project that is not a git repo works"
SRC16="$TMP/s16-src"; clone_src "$SRC16"
CONS16="$TMP/s16-cons"; build_consumer "$CONS16" nogit
run --version v0.1.0 --project "$CONS16"
assert_rc "non-git consumer installs" 0 "$IRC"
assert_true "correct installed" test -f "$CONS16/.agents/skills/correct/SKILL.md"
assert_true "lock installed" test -f "$CONS16/.opencode/cstack.lock.json"

# ------------------------------------ S17 relative project from other cwd ----

step "S17 relative --project path from a different cwd"
SRC17="$TMP/s17-src"; clone_src "$SRC17"
RELBASE="$TMP/s17-relbase"; mkdir -p "$RELBASE"
build_consumer "$RELBASE/re lative cons" bare
( cd -- "$RELBASE" && "$CUR" --version v0.1.0 --project "re lative cons" ) >"$OUT" 2>"$ERR"
IRC=$?
assert_rc "relative project path works" 0 "$IRC"
assert_true "installed into the relative consumer" \
    test -f "$RELBASE/re lative cons/.agents/skills/sharpen/SKILL.md"

# --------------------------------------------- S18 symlink collisions -------

step "S18 symlink collisions: refused, then replaced without outside damage"
SRC18="$TMP/s18-src"; clone_src "$SRC18"
OUTSIDE18="$TMP/s18-outside"; mkdir -p "$OUTSIDE18/correct"
printf 'OUTSIDE CORRECT\n' > "$OUTSIDE18/correct/SKILL.md"
CONS18="$TMP/s18-cons"; build_consumer "$CONS18" bare
mkdir -p "$CONS18/.agents/skills" "$CONS18/.claude/skills/sharpen"
ln -s "$OUTSIDE18/correct" "$CONS18/.agents/skills/correct"
printf 'user sharpen dir\n' > "$CONS18/.claude/skills/sharpen/SKILL.md"
run --version v0.1.0 --project "$CONS18"
assert_rc "symlinked skill path refused" 1 "$IRC"
file_is "refusal left the symlink target intact" "$OUTSIDE18/correct/SKILL.md" 'OUTSIDE CORRECT'
assert_false "refusal installed nothing else" test -e "$CONS18/.agents/skills/sharpen"
file_is "refusal left the user dir at the link path intact" \
    "$CONS18/.claude/skills/sharpen/SKILL.md" 'user sharpen dir'
run --version v0.1.0 --project "$CONS18" --force
assert_rc "force replaces the collisions" 0 "$IRC"
assert_true "the skill copy is now a real directory" test -d "$CONS18/.agents/skills/correct"
assert_false "the skill copy is no longer a link" test -L "$CONS18/.agents/skills/correct"
file_is "tag content installed" "$CONS18/.agents/skills/correct/SKILL.md" 'correct v0.1.0'
file_is "the old link target still intact (replaced, not followed)" \
    "$OUTSIDE18/correct/SKILL.md" 'OUTSIDE CORRECT'
assert_true "the link path is now a symlink" test -L "$CONS18/.claude/skills/sharpen"
assert_eq "the link path points at the vendored copy" \
    "../../.agents/skills/sharpen" "$(readlink "$CONS18/.claude/skills/sharpen")"

# ------------------------------------------- S19 lock path collisions --------

step "S19 lock path collisions (directory / symlink elsewhere)"
SRC19="$TMP/s19-src"; clone_src "$SRC19"
CONS19="$TMP/s19-cons"; build_consumer "$CONS19" bare
mkdir -p "$CONS19/.opencode/cstack.lock.json"
printf 'inside the lock dir\n' > "$CONS19/.opencode/cstack.lock.json/keep"
run --version v0.1.0 --project "$CONS19"
assert_rc "lock dir refused without --force" 1 "$IRC"
run --version v0.1.0 --project "$CONS19" --force
assert_rc "lock dir replaced with --force" 0 "$IRC"
assert_true "lock is now a regular file" test -f "$CONS19/.opencode/cstack.lock.json"
assert_false "lock is no longer a directory" test -d "$CONS19/.opencode/cstack.lock.json"
# a symlinked lock: replaced itself, never written through
LK19="$TMP/s19-lock-target"; printf 'target lock\n' > "$LK19"
CONS19B="$TMP/s19b-cons"; build_consumer "$CONS19B" bare
mkdir -p "$CONS19B/.opencode"
ln -s "$LK19" "$CONS19B/.opencode/cstack.lock.json"
run --version v0.1.0 --project "$CONS19B"
assert_rc "symlinked lock refused without --force" 1 "$IRC"
run --version v0.1.0 --project "$CONS19B" --force
assert_rc "symlinked lock replaced with --force" 0 "$IRC"
assert_false "lock is no longer a symlink" test -L "$CONS19B/.opencode/cstack.lock.json"
file_is "the symlink's target content untouched" "$LK19" 'target lock'
assert_file_has "the real lock written in its place" \
    "$CONS19B/.opencode/cstack.lock.json" '"tag": "v0.1.0"'

# ------------------------------------ S20 broken layout components ----------

step "S20 layout components that are not real directories (hard errors)"
SRC20="$TMP/s20-src"; clone_src "$SRC20"
CONS20="$TMP/s20-cons"; build_consumer "$CONS20" bare
printf 'not a dir\n' > "$CONS20/.agents"
run --version v0.1.0 --project "$CONS20"
assert_rc ".agents as a regular file is refused" 1 "$IRC"
run --version v0.1.0 --project "$CONS20" --force
assert_rc ".agents as a file refuses even with --force" 1 "$IRC"
assert_false "nothing else was created" test -e "$CONS20/.claude"
assert_false "no lock directory appeared" test -e "$CONS20/.opencode"
CLREAL20="$TMP/s20-claude-real"; mkdir -p "$CLREAL20"
CONS20B="$TMP/s20b-cons"; build_consumer "$CONS20B" bare
ln -s "$CLREAL20" "$CONS20B/.claude"
run --version v0.1.0 --project "$CONS20B"
assert_rc ".claude as a symlink is refused" 1 "$IRC"
run --version v0.1.0 --project "$CONS20B" --force
assert_rc ".claude as a symlink refuses even with --force" 1 "$IRC"
assert_eq "the dir behind the .claude link untouched" "" "$(ls -A "$CLREAL20")"

# ------------------------------ S21 hostile or junk entries in the tag ------

step "S21 hostile/junk entries inside a tag"
BADSRC="$TMP/s21-bad-src"
git -c init.defaultBranch=main init -q "$BADSRC" 2>/dev/null
mkdir -p "$BADSRC/skills/bad_id"
printf 'x\n' > "$BADSRC/skills/bad_id/SKILL.md"
printf 'loose note\n' > "$BADSRC/skills/notes.txt"
git -C "$BADSRC" add -A >/dev/null 2>&1
git -C "$BADSRC" -c user.name=T -c user.email=t@example.com commit -qm bad >/dev/null 2>&1
git -C "$BADSRC" tag -a v5.0.0 -m bad >/dev/null 2>&1
stage_only "$BADSRC"
CONS21="$TMP/s21-cons"; build_consumer "$CONS21" bare
run --version v5.0.0 --project "$CONS21"
assert_rc "invalid skill id in a tag is refused" 1 "$IRC"
assert_true "error names the bad id" err_has "bad_id"
assert_false "consumer untouched by the hostile tag" test -e "$CONS21/.agents"
# junk entries next to a valid skill: ignored, not vendored, not fatal
OKSRC="$TMP/s21-ok-src"
git -c init.defaultBranch=main init -q "$OKSRC" 2>/dev/null
mkdir -p "$OKSRC/skills/ok-skill"
printf 'ok\n' > "$OKSRC/skills/ok-skill/SKILL.md"
printf 'loose\n' > "$OKSRC/skills/README-fragment.md"
git -C "$OKSRC" add -A >/dev/null 2>&1
git -C "$OKSRC" -c user.name=T -c user.email=t@example.com commit -qm ok >/dev/null 2>&1
git -C "$OKSRC" tag v6.0.0 >/dev/null 2>&1
stage_only "$OKSRC"
CONS21B="$TMP/s21b-cons"; build_consumer "$CONS21B" bare
run --version v6.0.0 --project "$CONS21B"
assert_rc "a loose non-skill file does not fail the install" 0 "$IRC"
assert_true "the valid skill is installed" test -f "$CONS21B/.agents/skills/ok-skill/SKILL.md"
assert_false "the loose file is not vendored" test -e "$CONS21B/.agents/skills/README-fragment.md"
assert_true "ignored entries are reported" out_has "README-fragment.md"

# ------------------------------ S22 tag and same-named branch collision ----

step "S22 a tag and a same-named branch: the pin resolves the tag only"
CLSRC="$TMP/s22-src"
git -c init.defaultBranch=main init -q "$CLSRC" 2>/dev/null
mkdir -p "$CLSRC/skills/collide"
printf 'from the tag commit\n' > "$CLSRC/skills/collide/SKILL.md"
git -C "$CLSRC" add -A >/dev/null 2>&1
git -C "$CLSRC" -c user.name=T -c user.email=t@example.com commit -qm c1 >/dev/null 2>&1
git -C "$CLSRC" tag -a v1.2.3 -m collide >/dev/null 2>&1
S22_TAGC=$(git -C "$CLSRC" rev-parse 'refs/tags/v1.2.3^{commit}')
# a branch with the exact same name, on a newer commit
printf 'from the branch commit\n' > "$CLSRC/skills/collide/SKILL.md"
git -C "$CLSRC" add -A >/dev/null 2>&1
git -C "$CLSRC" -c user.name=T -c user.email=t@example.com commit -qm c2 >/dev/null 2>&1
S22_BRC=$(git -C "$CLSRC" rev-parse HEAD)
git -C "$CLSRC" branch v1.2.3 >/dev/null 2>&1
assert_true "fixture sanity: branch head differs from the tag" test "$S22_TAGC" != "$S22_BRC"
stage_only "$CLSRC"
CONS22="$TMP/s22-cons"; build_consumer "$CONS22" bare
run --version v1.2.3 --project "$CONS22"
assert_rc "install with a same-named branch succeeds" 0 "$IRC"
file_is "content comes from the tag commit, not the branch" \
    "$CONS22/.agents/skills/collide/SKILL.md" 'from the tag commit'
assert_file_has "lock pins the tag's commit" \
    "$CONS22/.opencode/cstack.lock.json" "\"commit\": \"$S22_TAGC\""
assert_false "lock does not pin the branch head" \
    grep -qF "\"commit\": \"$S22_BRC\"" "$CONS22/.opencode/cstack.lock.json"

# -------------------------- S23 symlink inside an existing skill copy --------

step "S23 a vendored copy containing a symlink: conflict before diff, never followed"
SRC23="$TMP/s23-src"; clone_src "$SRC23"
SECRET23="$TMP/s23-secret"; printf 'secret\n' > "$SECRET23"
CONS23="$TMP/s23-cons"; build_consumer "$CONS23" bare
mkdir -p "$CONS23/.agents/skills/correct"
printf 'correct v0.1.0\n' > "$CONS23/.agents/skills/correct/SKILL.md"   # matches the tag
ln -s "$SECRET23" "$CONS23/.agents/skills/correct/escape"
run --version v0.1.0 --project "$CONS23"
assert_rc "a copy with a nested symlink is refused" 1 "$IRC"
assert_true "refusal is the symlink rule, not a content diff" err_has "symbolic link"
assert_false "nothing else was installed" test -e "$CONS23/.agents/skills/sharpen"
assert_true "the nested link is untouched by the refusal" test -L "$CONS23/.agents/skills/correct/escape"
file_is "the file behind the link is intact" "$SECRET23" 'secret'
run --version v0.1.0 --project "$CONS23" --force
assert_rc "force replaces the polluted copy" 0 "$IRC"
file_is "clean tag content installed" "$CONS23/.agents/skills/correct/SKILL.md" 'correct v0.1.0'
assert_false "the nested link is gone" test -L "$CONS23/.agents/skills/correct/escape"
file_is "the file behind the old link still intact (removed, not followed)" "$SECRET23" 'secret'

# ------------------------------- S24 symlink inside a skill of the tag -------

step "S24 a tag whose skill contains a symlink is refused"
HAZSRC="$TMP/s24-src"
git -c init.defaultBranch=main init -q "$HAZSRC" 2>/dev/null
mkdir -p "$HAZSRC/skills/haz-skill"
printf 'hazard\n' > "$HAZSRC/skills/haz-skill/SKILL.md"
ln -s ../../../../../outside "$HAZSRC/skills/haz-skill/escape"
git -C "$HAZSRC" add -A >/dev/null 2>&1
git -C "$HAZSRC" -c user.name=T -c user.email=t@example.com commit -qm haz >/dev/null 2>&1
git -C "$HAZSRC" tag -a v7.0.0 -m haz >/dev/null 2>&1
stage_only "$HAZSRC"
CONS24="$TMP/s24-cons"; build_consumer "$CONS24" bare
run --version v7.0.0 --project "$CONS24"
assert_rc "tag with a symlink inside a skill is refused" 1 "$IRC"
assert_true "error names the skill" err_has "haz-skill"
assert_true "error says symbolic link" err_has "symbolic link"
assert_false "consumer untouched by the hostile tag" test -e "$CONS24/.agents"

# -------------------------------------------------------------- summary -----

printf '\n%d checks passed, %d failed.\n' "$PASS" "$FAIL"
if [ "$FAIL" -gt 0 ]; then
    printf 'TESTS FAILED\n'
    exit 1
fi
printf 'ALL TESTS PASSED\n'
exit 0
