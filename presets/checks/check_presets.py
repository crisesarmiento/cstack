#!/usr/bin/env python3
"""Preset cost-policy checker for cstack (oh-my-opencode-slim 3.0.7).

Python 3 standard library only: no third-party packages.

Policy source: rules/cost-and-models.md. Fail closed everywhere: a missing
file, unreadable allowlist, or parse error is an operational error (exit 2),
never a pass.

Checks (code -> rule):
  FALLBACK_NOT_DISABLED            fallback must be present with enabled
                                   exactly false. Upstream default is true;
                                   a model chain walked on failure can spend
                                   on an inherited paid route.
  DENIED_VENDOR_MODEL              no grok / xai / x.ai route anywhere a
                                   model id can appear (agents, presets,
                                   council seats, chain entries). The
                                   deny-list beats the allowlist.
  UNEVIDENCED_MODEL                every configured model id must be either
                                   a FILL_IN_* placeholder or an entry of
                                   the verified-free allowlist, which itself
                                   requires evidence. No slug or naming
                                   inference: OpenRouter ':free' suffixes are
                                   a hint, NVIDIA has no universal free
                                   naming, and neither counts as evidence.
  MODEL_CHAIN_FORBIDDEN            an array "model" is an ordered fallback
                                   chain upstream (on council seats too);
                                   chains are rejected outright, even when
                                   every entry is a placeholder or verified.
  ROLE_INHERITS_UNEVIDENCED_MODEL  every built-in role must be pinned with an
                                   explicit model or listed in
                                   disabled_agents; an entry present without
                                   a model fails the same way. Custom agents
                                   present under "agents" must carry models.
  COUNCIL_NOT_DISABLED             council must stay in disabled_agents:
                                   seat models come from the active council
                                   preset (council.presets.<name>.<seat>),
                                   which this file cannot verify, and
                                   disabling council is the upstream
                                   whole-chain switch (v3.0.7
                                   src/agents/council-agents.ts).
  OBSERVER_UNVERIFIED              observer must stay in disabled_agents or
                                   be pinned with a non-placeholder route: a
                                   placeholder leaves the role enabled
                                   without a usable verified route.
  INHERIT_MODEL_FORBIDDEN          inheritModelFrom is rejected: the followed
                                   session/orchestrator model is not
                                   evidenced in this file.
  SKILLS_REPLACEMENT_FORBIDDEN     agent entries must not define "skills"
                                   (replacement semantics upstream); use
                                   skills_add / skills_remove /
                                   skills_include_local instead.
  SKILLS_STAR_FORBIDDEN            no "*" in any skills list.
  SECRET_LIKE_VALUE                the raw text must not look like it carries
                                   a credential.
  ALLOWLIST_INVALID (operational)  the allowlist is the evidence record; a
                                   malformed, denied-vendor, duplicated, or
                                   out-of-scope-provider entry breaks it and
                                   aborts the run. Only "openrouter/" and
                                   "nvidia/" route ids may be allowlisted.
  CONFIG_STRUCTURE (operational)   unreadable or unparsable files, and model
                                   values of an invalid type (null, object,
                                   number, empty chain, non-string chain
                                   entries): these fail closed, they are
                                   never treated as a pinned route.

Usage:
  check_presets.py --scan presets [--allowlist FILE]
      Validate every top-level presets/*.jsonc (at least one must exist).
  check_presets.py --file PATH [--allowlist FILE]
      Validate one preset file (consumer integration mode: point this at the
      live .opencode/oh-my-opencode-slim.json[c]).
  check_presets.py --self-test FIXTURES_DIR
      Run fixtures/must-pass and fixtures/must-fail per manifest.json.

Exit codes: 0 policy satisfied, 1 policy violation, 2 operational error.
"""

import argparse
import datetime
import glob
import json
import os
import re
import sys

BUILTIN_ROLES = [
    "orchestrator",
    "explorer",
    "oracle",
    "designer",
    "fixer",
    "observer",
    "council",
    "councillor",
]

PLACEHOLDER_RE = re.compile(r"^FILL_IN_[A-Z0-9_]+$")
DENIED_VENDOR_RE = re.compile(r"(^|[^a-z0-9])(grok|xai|x\.ai)([^a-z0-9]|$)", re.IGNORECASE)
ALLOWED_ROUTE_PREFIXES = ("openrouter/", "nvidia/")
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{16,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9._-]{16,}"),
    re.compile(
        r"(?i)\b(api[_-]?key|secret|token|password)\b['\"]?\s*[:=]\s*['\"][^'\"\n]{8,}['\"]"
    ),
]
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def default_allowlist_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "free-route-allowlist.jsonc")


class Problems:
    """Collects policy violations and operational errors separately."""

    def __init__(self):
        self.policy = []  # exit 1
        self.operational = []  # exit 2

    def violation(self, code, where, message):
        self.policy.append((code, "%s: %s" % (where, message)))

    def operational_error(self, code, where, message):
        self.operational.append((code, "%s: %s" % (where, message)))

    def exit_code(self):
        if self.operational:
            return 2
        if self.policy:
            return 1
        return 0

    def all_codes(self):
        return [code for code, _ in self.policy] + [code for code, _ in self.operational]

    def report(self, stream):
        for code, text in self.policy:
            stream.write("%s: %s\n" % (code, text))
        for code, text in self.operational:
            stream.write("%s: %s\n" % (code, text))


def strip_jsonc(text):
    """Remove // and /* */ comments, string-aware. Line comments keep the
    trailing newline; string contents are preserved verbatim (including
    escaped quotes and '//' inside strings)."""
    out = []
    i = 0
    n = len(text)
    in_string = False
    while i < n:
        c = text[i]
        if in_string:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            if c == '"':
                in_string = False
            i += 1
            continue
        if c == '"':
            in_string = True
            out.append(c)
            i += 1
            continue
        if c == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                i += 1
            continue
        if c == "/" and i + 1 < n and text[i + 1] == "*":
            i += 2
            while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2
            continue
        out.append(c)
        i += 1
    return "".join(out)


def remove_trailing_commas(text):
    """Drop commas whose next non-whitespace character is } or ]. Only runs
    outside string literals, so commas inside string values are preserved."""
    out = []
    i = 0
    n = len(text)
    in_string = False
    while i < n:
        c = text[i]
        if in_string:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            if c == '"':
                in_string = False
            i += 1
            continue
        if c == '"':
            in_string = True
            out.append(c)
            i += 1
            continue
        if c == ",":
            j = i + 1
            while j < n and text[j] in " \t\r\n":
                j += 1
            if j < n and text[j] in "}]":
                i += 1
                continue
        out.append(c)
        i += 1
    return "".join(out)


def load_allowlist(path, problems):
    """Load the verified-free allowlist. Returns a set of admitted ids.

    The allowlist is the evidence record for rule 2 (an API key or a catalog
    listing is never permission to spend): every entry must carry where the
    $0 price was verified and when. Provider scope is part of the rule: only
    OpenRouter ('openrouter/...') and NVIDIA ('nvidia/...') route ids are
    admitted, with or without evidence. A broken entry is an operational
    error: the whole record cannot be trusted, so the run fails closed.
    """
    where = "allowlist %s" % path
    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw = fh.read()
    except OSError as exc:
        problems.operational_error("ALLOWLIST_INVALID", where, "unreadable: %s" % exc)
        return None
    try:
        data = json.loads(strip_jsonc(raw))
    except ValueError as exc:
        problems.operational_error("ALLOWLIST_INVALID", where, "not valid JSONC: %s" % exc)
        return None
    if not isinstance(data, dict) or not isinstance(data.get("routes"), list):
        problems.operational_error(
            "ALLOWLIST_INVALID", where, 'expected an object with a "routes" array'
        )
        return None
    admitted = set()
    for index, entry in enumerate(data["routes"]):
        entry_where = "%s route[%d]" % (where, index)
        if not isinstance(entry, dict):
            problems.operational_error("ALLOWLIST_INVALID", entry_where, "entry is not an object")
            continue
        rid = entry.get("id")
        if not isinstance(rid, str) or not rid.strip():
            problems.operational_error("ALLOWLIST_INVALID", entry_where, "missing non-empty id")
            continue
        if DENIED_VENDOR_RE.search(rid):
            problems.operational_error(
                "ALLOWLIST_INVALID",
                entry_where,
                "deny-list route %r cannot be allowlisted (rule: Grok never in "
                "OpenCode automatic chains)" % rid,
            )
            continue
        if not rid.startswith(ALLOWED_ROUTE_PREFIXES):
            problems.operational_error(
                "ALLOWLIST_INVALID",
                entry_where,
                "route %r is outside the requested provider scope: only "
                "'openrouter/...' and 'nvidia/...' route ids may be "
                "allowlisted (rules/cost-and-models.md rule 1)" % rid,
            )
            continue
        if rid in admitted:
            problems.operational_error("ALLOWLIST_INVALID", entry_where, "duplicate id %r" % rid)
            continue
        evidence = entry.get("evidence")
        if not isinstance(evidence, dict):
            problems.operational_error(
                "ALLOWLIST_INVALID", entry_where, "route %r has no evidence object" % rid
            )
            continue
        source = evidence.get("source")
        if not isinstance(source, str) or not re.match(r"^https?://", source):
            problems.operational_error(
                "ALLOWLIST_INVALID",
                entry_where,
                "route %r evidence.source must be the URL of the page where $0 "
                "pricing was verified" % rid,
            )
            continue
        checked = evidence.get("checked")
        if not isinstance(checked, str) or not DATE_RE.match(checked):
            problems.operational_error(
                "ALLOWLIST_INVALID",
                entry_where,
                "route %r evidence.checked must be an ISO date (YYYY-MM-DD)" % rid,
            )
            continue
        try:
            datetime.date.fromisoformat(checked)
        except ValueError:
            problems.operational_error(
                "ALLOWLIST_INVALID", entry_where, "route %r evidence.checked is not a real date" % rid
            )
            continue
        quote = evidence.get("quote")
        if not isinstance(quote, str) or not quote.strip():
            problems.operational_error(
                "ALLOWLIST_INVALID",
                entry_where,
                "route %r evidence.quote must quote the page text proving $0 "
                "pricing (naming conventions are not evidence)" % rid,
            )
            continue
        admitted.add(rid)
    if problems.operational:
        return None
    return admitted


def check_model_value(value, where, admitted, problems):
    """Apply the model policy to one model value, failing closed on shape.

    Upstream v3.0.7: a scalar model is one route id; an array model is an
    ordered fallback chain (on council seats too). Policy: scalars only -
    arrays are rejected outright, and a value of an invalid type (null,
    object, number, empty chain, non-string chain entry) is an operational
    error, never a silently-pinned route.
    """
    if not isinstance(value, (str, list, dict)):
        problems.operational_error(
            "CONFIG_STRUCTURE",
            where + ".model",
            "model must be a route id string or an array of ids, got %s"
            % type(value).__name__,
        )
        return
    if isinstance(value, dict):
        problems.operational_error(
            "CONFIG_STRUCTURE",
            where + ".model",
            "model must be a route id string or an array of ids, not an object",
        )
        return
    if isinstance(value, list):
        if not value:
            problems.operational_error(
                "CONFIG_STRUCTURE",
                where + ".model",
                "model chain is empty; pin a scalar route instead",
            )
            return
        problems.violation(
            "MODEL_CHAIN_FORBIDDEN",
            where + ".model",
            "an array model is an ordered fallback chain upstream and is "
            "rejected even when every entry is a placeholder or verified; pin "
            "one scalar route (rules/cost-and-models.md rule 1)",
        )
        for index, entry in enumerate(value):
            label = "model[%d]" % index
            if isinstance(entry, str):
                rid = entry
            elif isinstance(entry, dict) and isinstance(entry.get("id"), str) and entry["id"]:
                rid = entry["id"]
                label += ".id"
            else:
                problems.operational_error(
                    "CONFIG_STRUCTURE",
                    "%s.%s" % (where, label),
                    "chain entry must be a route id string or {id, variant}",
                )
                continue
            check_route_id(rid, "%s.%s" % (where, label), admitted, problems)
        return
    check_route_id(value, where + ".model", admitted, problems)


def check_route_id(rid, entry_where, admitted, problems):
    """Deny-list, then fail-closed evidence check, for one route id."""
    if DENIED_VENDOR_RE.search(rid):
        problems.violation(
            "DENIED_VENDOR_MODEL",
            entry_where,
            "route %r matches the Grok/xAI deny-list; Grok is never allowed "
            "in an OpenCode automatic chain (rules/cost-and-models.md rule 3)" % rid,
        )
        return
    if PLACEHOLDER_RE.match(rid):
        return
    if admitted is not None and rid in admitted:
        return
    problems.violation(
        "UNEVIDENCED_MODEL",
        entry_where,
        "route %r is neither a FILL_IN_* placeholder nor in the verified-free "
        "allowlist with evidence; verify the route is free today and add it "
        "with evidence, or use a placeholder / disable the role "
        "(rules/cost-and-models.md rule 1)" % rid,
    )


def agent_entries(config, problems):
    """Yield (where, name, entry) for every agent entry: root agents first,
    then every preset block entry, then council seat entries."""
    agents = config.get("agents")
    if agents is not None:
        if not isinstance(agents, dict):
            problems.operational_error("CONFIG_STRUCTURE", "agents", "must be an object")
            agents = None
    if agents:
        for name, entry in sorted(agents.items()):
            if isinstance(entry, dict):
                yield ("agents.%s" % name, name, entry)
    presets = config.get("presets")
    if presets is not None:
        if not isinstance(presets, dict):
            problems.operational_error("CONFIG_STRUCTURE", "presets", "must be an object")
            presets = None
    if presets:
        for pname, block in sorted(presets.items()):
            if not isinstance(block, dict):
                problems.operational_error(
                    "CONFIG_STRUCTURE", "presets.%s" % pname, "must be an object"
                )
                continue
            for name, entry in sorted(block.items()):
                if isinstance(entry, dict):
                    yield ("presets.%s.%s" % (pname, name), name, entry)
    council = config.get("council")
    if isinstance(council, dict) and isinstance(council.get("presets"), dict):
        for pname, block in sorted(council["presets"].items()):
            if not isinstance(block, dict):
                problems.operational_error(
                    "CONFIG_STRUCTURE", "council.presets.%s" % pname, "must be an object"
                )
                continue
            for name, entry in sorted(block.items()):
                if isinstance(entry, dict):
                    yield ("council.presets.%s.%s" % (pname, name), name, entry)


def validate_file(path, allowlist_path, problems):
    """Validate one preset file against the policy. The allowlist is loaded
    per file so fixtures can exercise different evidence records."""
    where = "preset %s" % path
    admitted = load_allowlist(allowlist_path, problems)
    if problems.operational:
        return
    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw = fh.read()
    except OSError as exc:
        problems.operational_error("CONFIG_STRUCTURE", where, "unreadable: %s" % exc)
        return
    for pattern in SECRET_PATTERNS:
        for match in pattern.finditer(raw):
            problems.violation(
                "SECRET_LIKE_VALUE",
                where,
                "text at offset %d looks like a credential; presets never carry "
                "keys or tokens (rules/cost-and-models.md rule 2)" % match.start(),
            )
    try:
        config = json.loads(remove_trailing_commas(strip_jsonc(raw)))
    except ValueError as exc:
        problems.operational_error("CONFIG_STRUCTURE", where, "not valid JSONC: %s" % exc)
        return
    if not isinstance(config, dict):
        problems.operational_error("CONFIG_STRUCTURE", where, "top level is not an object")
        return

    # P1: fallback failover must be explicitly disabled.
    fallback = config.get("fallback")
    if not isinstance(fallback, dict):
        problems.violation(
            "FALLBACK_NOT_DISABLED",
            where,
            '"fallback" is absent or not an object; upstream default is enabled '
            "and a chain walked on failure can spend on an inherited route",
        )
    elif fallback.get("enabled") is not False:
        problems.violation(
            "FALLBACK_NOT_DISABLED",
            where + ".fallback.enabled",
            "must be exactly false (upstream default is true); keep foreground "
            "model-chain failover off (rules/cost-and-models.md rule 1)",
        )

    # Roster: what this file disables (its own list only; a list here
    # replaces the user-level one upstream, so treat absence as nothing
    # disabled by this file - the conservative reading).
    disabled = []
    disabled_raw = config.get("disabled_agents")
    if disabled_raw is not None:
        if not isinstance(disabled_raw, list) or not all(
            isinstance(item, str) for item in disabled_raw
        ):
            problems.operational_error(
                "CONFIG_STRUCTURE", where + ".disabled_agents", "must be an array of strings"
            )
        else:
            disabled = disabled_raw
    disabled_set = set(disabled)

    # Per-entry checks everywhere a model, inheritance directive, or skills
    # grant can appear (root agents, preset blocks, council seats).
    for entry_where, name, entry in agent_entries(config, problems):
        if "inheritModelFrom" in entry:
            problems.violation(
                "INHERIT_MODEL_FORBIDDEN",
                entry_where + ".inheritModelFrom",
                "the followed session/orchestrator model is not evidenced in "
                "this file; pin an explicit route instead",
            )
        if "model" in entry:
            check_model_value(entry["model"], entry_where, admitted, problems)
        if "skills" in entry:
            problems.violation(
                "SKILLS_REPLACEMENT_FORBIDDEN",
                entry_where + ".skills",
                'defining "skills" replaces the inherited grant list upstream; '
                "use skills_add / skills_remove / skills_include_local instead",
            )
        for key in ("skills", "skills_add", "skills_remove"):
            value = entry.get(key)
            if isinstance(value, list) and "*" in value:
                problems.violation(
                    "SKILLS_STAR_FORBIDDEN",
                    "%s.%s" % (entry_where, key),
                    '"*" grant is forbidden; name the skills you want to add '
                    "or remove",
                )

    # P4 roster: only a ROOT agents entry guarantees the route regardless of
    # which preset is active (upstream: root agents beat preset entries). A
    # pin that exists only inside a preset block does not satisfy the roster.
    agents_map = config.get("agents") if isinstance(config.get("agents"), dict) else {}
    root_models = {
        name: entry["model"]
        for name, entry in agents_map.items()
        if isinstance(entry, dict) and "model" in entry
    }
    pinned = set(root_models)
    for name in sorted(agents_map):
        if name in BUILTIN_ROLES:
            continue
        entry = agents_map[name]
        if isinstance(entry, dict) and name not in pinned:
            problems.violation(
                "ROLE_INHERITS_UNEVIDENCED_MODEL",
                "agents.%s" % name,
                "custom agent entry has no explicit model; it would inherit an "
                "unverified route - pin it or remove the entry",
            )
    for role in BUILTIN_ROLES:
        if role in pinned:
            continue
        if role in disabled_set:
            continue
        problems.violation(
            "ROLE_INHERITS_UNEVIDENCED_MODEL",
            "agents.%s" % role,
            "built-in role is neither pinned with a model in root agents nor "
            "listed in disabled_agents; it would inherit the active preset's "
            "primary model, which this policy cannot verify - pin it or "
            "disable it (presets/README.md, roster policy)",
        )

    # Council: disabling "council" is the upstream whole-chain switch (v3.0.7
    # src/agents/council-agents.ts returns an empty seat list when council is
    # disabled). A pinned council agent model does NOT pin the seats: seat
    # models come from the active council preset, which this file cannot
    # verify unless it defines that preset itself. Council stays disabled.
    if "council" not in disabled_set:
        problems.violation(
            "COUNCIL_NOT_DISABLED",
            "disabled_agents",
            "council is not disabled; its seats take models from the active "
            "council preset (council.presets.<name>.<seat>), which this file "
            "cannot verify - keep council in disabled_agents. Re-enabling "
            "requires explicitly configured verified seats and a reviewed "
            "policy change (rules/cost-and-models.md rule 1)",
        )

    # Observer: a placeholder pin leaves the role enabled without a usable
    # verified route. Observer stays disabled or is filled with an evidenced
    # (non-placeholder) route; the evidence itself is checked above.
    if "observer" not in disabled_set:
        observer_model = root_models.get("observer")
        filled = isinstance(observer_model, str) and not PLACEHOLDER_RE.match(observer_model)
        if not filled:
            problems.violation(
                "OBSERVER_UNVERIFIED",
                "agents.observer",
                "observer is enabled but not filled with a verified route: "
                "keep it in disabled_agents or pin a route from your "
                "evidenced allowlist (it must also be vision-capable)",
            )


def scan_directory(directory, allowlist_path):
    files = sorted(glob.glob(os.path.join(directory, "*.jsonc")))
    problems = Problems()
    if not files:
        problems.operational_error(
            "CONFIG_STRUCTURE", "scan %s" % directory, "no .jsonc preset templates found"
        )
    for path in files:
        validate_file(path, allowlist_path, problems)
    return problems


def self_test(fixtures_dir):
    """Run the fixture suite. Every *.jsonc under the fixtures directory must
    be listed in manifest.json, and every manifest path must exist; drift in
    either direction fails. must-pass files must exit 0; must-fail files must
    exit non-zero and report every expected code."""
    problems = Problems()
    manifest_path = os.path.join(fixtures_dir, "manifest.json")
    try:
        with open(manifest_path, "r", encoding="utf-8") as fh:
            manifest = json.load(fh)
    except OSError as exc:
        problems.operational_error("CONFIG_STRUCTURE", manifest_path, "unreadable: %s" % exc)
        return problems
    except ValueError as exc:
        problems.operational_error("CONFIG_STRUCTURE", manifest_path, "invalid JSON: %s" % exc)
        return problems
    if not isinstance(manifest, dict):
        problems.operational_error("CONFIG_STRUCTURE", manifest_path, "must be an object")
        return problems

    on_disk = set()
    for root, _dirs, names in os.walk(fixtures_dir):
        for name in names:
            if name.endswith(".jsonc"):
                rel = os.path.relpath(os.path.join(root, name), fixtures_dir)
                on_disk.add(rel)
    listed = set(manifest.keys())
    for rel in sorted(on_disk - listed):
        problems.operational_error(
            "FIXTURE_DRIFT", rel, "fixture file is not listed in manifest.json"
        )
    for rel in sorted(listed - on_disk):
        problems.operational_error(
            "FIXTURE_DRIFT", rel, "manifest entry has no fixture file"
        )

    failures = 0
    for rel in sorted(listed & on_disk):
        spec = manifest[rel]
        if not isinstance(spec, dict):
            problems.operational_error("FIXTURE_DRIFT", rel, "manifest entry must be an object")
            continue
        path = os.path.join(fixtures_dir, rel)
        allowlist = spec.get("allowlist")
        allowlist_path = (
            os.path.join(fixtures_dir, allowlist)
            if allowlist
            else default_allowlist_path()
        )
        run = Problems()
        validate_file(path, allowlist_path, run)
        code = run.exit_code()
        expected_codes = spec.get("codes", [])
        expect_operational = bool(spec.get("operational", False))
        if rel.startswith("must-pass" + os.sep):
            if code != 0:
                failures += 1
                print("FAIL (expected pass): %s" % rel)
                run.report(sys.stdout)
            else:
                print("ok (passes): %s" % rel)
        else:
            if code == 0:
                failures += 1
                print("FAIL (expected violation, passed instead): %s" % rel)
                continue
            if expect_operational and code != 2:
                failures += 1
                print("FAIL (expected operational error 2, got %d): %s" % (code, rel))
                run.report(sys.stdout)
                continue
            if not expect_operational and code != 1:
                failures += 1
                print("FAIL (expected policy violation 1, got %d): %s" % (code, rel))
                run.report(sys.stdout)
                continue
            missing = [c for c in expected_codes if c not in run.all_codes()]
            extra = [c for c in run.all_codes() if c not in expected_codes]
            if missing or extra:
                failures += 1
                print(
                    "FAIL (expected codes %s, got %s): %s"
                    % (", ".join(expected_codes), ", ".join(run.all_codes()), rel)
                )
                run.report(sys.stdout)
            else:
                print("ok (violates %s): %s" % (", ".join(expected_codes), rel))
    if failures:
        problems.operational_error("FIXTURE_DRIFT", fixtures_dir, "%d fixture(s) misbehaved" % failures)
    return problems


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--scan", metavar="DIR", help="validate every top-level DIR/*.jsonc")
    target.add_argument("--file", metavar="PATH", help="validate one preset file")
    target.add_argument("--self-test", metavar="DIR", help="run the fixture suite under DIR")
    parser.add_argument(
        "--allowlist",
        metavar="PATH",
        default=None,
        help="verified-free allowlist (default: the one shipped beside this script)",
    )
    args = parser.parse_args(argv)
    allowlist = args.allowlist if args.allowlist else default_allowlist_path()

    if args.self_test:
        problems = self_test(args.self_test)
    elif args.scan:
        problems = scan_directory(args.scan, allowlist)
    else:
        problems = Problems()
        validate_file(args.file, allowlist, problems)

    problems.report(sys.stderr)
    code = problems.exit_code()
    if code == 0:
        print("OK: preset cost policy satisfied.")
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
